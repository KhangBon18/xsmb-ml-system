"""Tests for Phase 2C database repositories."""

from __future__ import annotations

import json
from pathlib import Path

import pytest

from xsmb.config import (
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
    TARGET_LOTO_2D_ALL_PRIZES,
)
from xsmb.database.connection import create_engine_from_url, create_session_factory
from xsmb.database.models import FeatureSnapshot, ModelRun, Prediction, drop_db, init_db
from xsmb.database.repository import (
    DrawRepository,
    FeatureSnapshotRepository,
    ModelRunRepository,
    PredictionRepository,
    PrizeRepository,
    RawPageRepository,
    TargetRepository,
)


@pytest.fixture
def repository_session(tmp_path: Path):
    """Create a temporary SQLite session for repository tests."""
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'repository.sqlite3'}")
    init_db(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session

    drop_db(engine)
    engine.dispose()


@pytest.fixture
def draw_rows_with_special_leading_zero(
    sample_draw_rows: list[dict[str, object]]
) -> list[dict[str, object]]:
    """Return valid rows where special-prize targets must preserve zeros."""
    rows = [dict(row) for row in sample_draw_rows]
    rows[0]["winning_number"] = "45008"
    rows[1]["winning_number"] = "12999"
    return rows


def test_raw_page_repository_insert_get_and_avoid_duplicate_checksum(
    repository_session,
) -> None:
    repo = RawPageRepository(repository_session)

    first = repo.insert(
        source_name="unit_test",
        source_url="https://example.test/xsmb",
        draw_date="2024-01-15",
        raw_html="<html>first</html>",
        raw_text="first",
        checksum="checksum-1",
        parser_version="v1",
    )
    duplicate = repo.insert(
        source_name="unit_test",
        source_url="https://example.test/xsmb-copy",
        draw_date="2024-01-15",
        raw_html="<html>duplicate</html>",
        raw_text="duplicate",
        checksum="checksum-1",
        parser_version="v1",
    )

    assert repo.get_by_checksum("checksum-1").id == first.id
    assert duplicate.id == first.id
    assert repository_session.query(type(first)).count() == 1


def test_draw_repository_create_get_idempotent_and_update_status(
    repository_session,
) -> None:
    repo = DrawRepository(repository_session)

    draw = repo.create_or_get(draw_date="2024-01-15", source_name="unit_test")
    duplicate = repo.create_or_get(draw_date="2024-01-15", source_name="other")
    updated = repo.update_status(draw, "validated")

    assert duplicate.id == draw.id
    assert repo.get_by_draw_date("2024-01-15").id == draw.id
    assert updated.status == "validated"
    assert draw.region == "mien_bac"
    assert draw.province == "XSMB"


def test_prize_repository_saves_and_reads_27_prizes_exactly(
    repository_session,
    draw_rows_with_special_leading_zero: list[dict[str, object]],
) -> None:
    draw = DrawRepository(repository_session).create_or_get(draw_date="2024-01-15")
    prize_repo = PrizeRepository(repository_session)

    saved = prize_repo.save_prizes(draw, draw_rows_with_special_leading_zero)
    repository_session.expire_all()
    by_date = prize_repo.list_by_draw_date("2024-01-15")
    by_id = prize_repo.list_by_draw_id(draw.id)

    assert len(saved) == 27
    assert len(by_date) == 27
    assert [(p.prize_tier, p.prize_index, p.winning_number) for p in by_date] == [
        (row["prize_tier"], row["prize_index"], row["winning_number"])
        for row in draw_rows_with_special_leading_zero
    ]
    assert [(p.prize_tier, p.prize_index) for p in by_id] == [
        (row["prize_tier"], row["prize_index"])
        for row in draw_rows_with_special_leading_zero
    ]
    assert by_date[0].winning_number == "45008"


def test_prize_repository_duplicate_insert_is_idempotent(
    repository_session,
    draw_rows_with_special_leading_zero: list[dict[str, object]],
) -> None:
    draw = DrawRepository(repository_session).create_or_get(draw_date="2024-01-15")
    prize_repo = PrizeRepository(repository_session)

    first = prize_repo.save_prizes(draw, draw_rows_with_special_leading_zero)
    second = prize_repo.save_prizes(draw, draw_rows_with_special_leading_zero)

    assert [prize.id for prize in second] == [prize.id for prize in first]
    assert len(prize_repo.list_by_draw_id(draw.id)) == 27


def test_prize_repository_duplicate_conflict_raises(
    repository_session,
    draw_rows_with_special_leading_zero: list[dict[str, object]],
) -> None:
    draw = DrawRepository(repository_session).create_or_get(draw_date="2024-01-15")
    prize_repo = PrizeRepository(repository_session)
    prize_repo.save_prizes(draw, draw_rows_with_special_leading_zero)
    conflicting_rows = [dict(row) for row in draw_rows_with_special_leading_zero]
    conflicting_rows[0]["winning_number"] = "45009"

    with pytest.raises(ValueError, match="Conflicting prize"):
        prize_repo.save_prizes(draw, conflicting_rows)


@pytest.mark.parametrize(
    ("target_type", "expected_count", "expected_winner"),
    [
        (TARGET_LOTO_2D_ALL_PRIZES, 100, "08"),
        (TARGET_DB_2CANG, 100, "08"),
        (TARGET_DB_3CANG, 1000, "008"),
    ],
)
def test_target_repository_generates_expected_target_rows_idempotently(
    repository_session,
    draw_rows_with_special_leading_zero: list[dict[str, object]],
    target_type: str,
    expected_count: int,
    expected_winner: str,
) -> None:
    draw = DrawRepository(repository_session).create_or_get(draw_date="2024-01-15")
    PrizeRepository(repository_session).save_prizes(draw, draw_rows_with_special_leading_zero)
    target_repo = TargetRepository(repository_session)

    first = target_repo.generate_and_save_targets(draw.id, target_type)
    second = target_repo.generate_and_save_targets(draw.id, target_type)
    by_date = target_repo.list_by_draw_date_and_target_type("2024-01-15", target_type)

    assert len(first) == expected_count
    assert len(second) == expected_count
    assert len(by_date) == expected_count
    assert [target.id for target in second] == [target.id for target in first]
    assert len({target.candidate_number for target in by_date}) == expected_count
    winner = next(
        target for target in by_date if target.candidate_number == expected_winner
    )
    assert winner.label == 1
    assert winner.hit_count >= 1


def test_target_repository_special_targets_use_only_special_prize(
    repository_session,
    draw_rows_with_special_leading_zero: list[dict[str, object]],
) -> None:
    draw = DrawRepository(repository_session).create_or_get(draw_date="2024-01-15")
    PrizeRepository(repository_session).save_prizes(draw, draw_rows_with_special_leading_zero)
    target_repo = TargetRepository(repository_session)

    db_2cang = target_repo.generate_and_save_targets(draw, TARGET_DB_2CANG)
    db_3cang = target_repo.generate_and_save_targets(draw, TARGET_DB_3CANG)

    assert next(t for t in db_2cang if t.candidate_number == "08").label == 1
    assert next(t for t in db_2cang if t.candidate_number == "99").label == 0
    assert next(t for t in db_3cang if t.candidate_number == "008").label == 1
    assert next(t for t in db_3cang if t.candidate_number == "999").label == 0


def test_feature_snapshot_repository_basic_insert_and_list(repository_session) -> None:
    repo = FeatureSnapshotRepository(repository_session)
    payload = {"freq_30": 2}

    snapshot = repo.insert(
        target_date="2024-01-16",
        target_type=TARGET_LOTO_2D_ALL_PRIZES,
        candidate_number="05",
        feature_json=json.dumps(payload),
        label=1,
        feature_version="v1",
    )
    listed = repo.list(target_date="2024-01-16", target_type=TARGET_LOTO_2D_ALL_PRIZES)

    assert isinstance(snapshot, FeatureSnapshot)
    assert len(listed) == 1
    assert json.loads(listed[0].feature_json) == payload


def test_model_run_repository_basic_create_get_and_list(repository_session) -> None:
    repo = ModelRunRepository(repository_session)

    run = repo.create(
        run_name="unit-run",
        model_name="baseline",
        target_type=TARGET_DB_2CANG,
        feature_version="v1",
        params_json=json.dumps({"window": 30}),
    )
    listed = repo.list(target_type=TARGET_DB_2CANG)

    assert isinstance(run, ModelRun)
    assert repo.get(run.id).id == run.id
    assert [item.id for item in listed] == [run.id]


def test_prediction_repository_basic_save_and_list_top_k(repository_session) -> None:
    run = ModelRunRepository(repository_session).create(
        run_name="unit-run",
        model_name="baseline",
        target_type=TARGET_DB_2CANG,
        feature_version="v1",
    )
    repo = PredictionRepository(repository_session)

    saved = repo.save_predictions(
        prediction_date="2024-01-16",
        target_type=TARGET_DB_2CANG,
        model_run_id=run.id,
        predictions=[
            {"candidate_number": "05", "score": 0.2, "rank": 2},
            {"candidate_number": "08", "score": 0.4, "rank": 1},
            {"candidate_number": "09", "score": 0.1, "rank": 3},
        ],
    )
    top_two = repo.list_top_k(
        prediction_date="2024-01-16",
        target_type=TARGET_DB_2CANG,
        model_run_id=run.id,
        k=2,
    )

    assert all(isinstance(item, Prediction) for item in saved)
    assert [item.candidate_number for item in top_two] == ["08", "05"]
    assert [item.rank for item in top_two] == [1, 2]
