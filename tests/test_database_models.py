"""Tests for Phase 2B SQLAlchemy ORM models and schema."""

from __future__ import annotations

import json
from pathlib import Path

import pytest
from sqlalchemy import inspect, text
from sqlalchemy.exc import IntegrityError

from xsmb.database.connection import create_engine_from_url, create_session_factory
from xsmb.database.models import (
    Draw,
    FeatureSnapshot,
    ModelRun,
    Prize,
    RawPage,
    Target,
    drop_db,
    init_db,
)


@pytest.fixture
def sqlite_session(tmp_path: Path):
    """Create a temporary SQLite session with all ORM tables."""
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'models.sqlite3'}")
    init_db(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session

    drop_db(engine)
    engine.dispose()


def test_all_tables_can_be_created_in_temporary_sqlite(tmp_path: Path) -> None:
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'schema.sqlite3'}")
    init_db(engine)

    table_names = set(inspect(engine).get_table_names())

    assert table_names == {
        "raw_pages",
        "draws",
        "prizes",
        "targets",
        "feature_snapshots",
        "model_runs",
        "predictions",
    }


def test_unique_draw_date_constraint_works(sqlite_session) -> None:
    sqlite_session.add_all(
        [
            Draw(draw_date="2024-01-15", source_name="source_a"),
            Draw(draw_date="2024-01-15", source_name="source_b"),
        ]
    )

    with pytest.raises(IntegrityError):
        sqlite_session.commit()


def test_prize_winning_number_preserves_leading_zero(sqlite_session) -> None:
    draw = Draw(draw_date="2024-01-16")
    sqlite_session.add(draw)
    sqlite_session.flush()

    sqlite_session.add(
        Prize(
            draw_id=draw.id,
            prize_tier="special",
            prize_index=0,
            winning_number="00512",
            number_length=5,
        )
    )
    sqlite_session.commit()

    prize = sqlite_session.query(Prize).one()
    assert prize.winning_number == "00512"
    assert isinstance(prize.winning_number, str)


def test_target_candidate_number_preserves_leading_zero(sqlite_session) -> None:
    draw = Draw(draw_date="2024-01-17")
    sqlite_session.add(draw)
    sqlite_session.flush()

    sqlite_session.add(
        Target(
            draw_id=draw.id,
            draw_date="2024-01-17",
            target_type="db_3cang",
            candidate_number="008",
            label=1,
            hit_count=1,
        )
    )
    sqlite_session.commit()

    target = sqlite_session.query(Target).one()
    assert target.candidate_number == "008"
    assert isinstance(target.candidate_number, str)


def test_foreign_keys_reject_prize_without_draw(sqlite_session) -> None:
    sqlite_session.add(
        Prize(
            draw_id=999,
            prize_tier="special",
            prize_index=0,
            winning_number="12345",
            number_length=5,
        )
    )

    with pytest.raises(IntegrityError):
        sqlite_session.commit()


def test_unique_prize_per_draw_tier_index(sqlite_session) -> None:
    draw = Draw(draw_date="2024-01-18")
    sqlite_session.add(draw)
    sqlite_session.flush()

    sqlite_session.add_all(
        [
            Prize(
                draw_id=draw.id,
                prize_tier="seventh",
                prize_index=0,
                winning_number="05",
                number_length=2,
            ),
            Prize(
                draw_id=draw.id,
                prize_tier="seventh",
                prize_index=0,
                winning_number="09",
                number_length=2,
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        sqlite_session.commit()


def test_unique_target_per_draw_type_candidate(sqlite_session) -> None:
    draw = Draw(draw_date="2024-01-19")
    sqlite_session.add(draw)
    sqlite_session.flush()

    sqlite_session.add_all(
        [
            Target(
                draw_id=draw.id,
                draw_date="2024-01-19",
                target_type="db_2cang",
                candidate_number="05",
                label=1,
                hit_count=1,
            ),
            Target(
                draw_id=draw.id,
                draw_date="2024-01-19",
                target_type="db_2cang",
                candidate_number="05",
                label=1,
                hit_count=1,
            ),
        ]
    )

    with pytest.raises(IntegrityError):
        sqlite_session.commit()


def test_json_text_fields_store_and_reload_json_strings(sqlite_session) -> None:
    feature_payload = {"freq_30": 4, "current_gap": 12}
    params_payload = {"C": 1.0}
    metrics_payload = {"brier_score": 0.18}

    feature_snapshot = FeatureSnapshot(
        target_date="2024-01-20",
        target_type="loto_2d_all_prizes",
        candidate_number="05",
        feature_json=json.dumps(feature_payload),
        label=1,
        feature_version="v1",
    )
    model_run = ModelRun(
        run_name="unit-test-run",
        model_name="logistic",
        target_type="loto_2d_all_prizes",
        feature_version="v1",
        train_from="2024-01-01",
        train_to="2024-01-10",
        test_from="2024-01-11",
        test_to="2024-01-20",
        params_json=json.dumps(params_payload),
        metrics_json=json.dumps(metrics_payload),
        artifact_path="data/models/unit-test.joblib",
    )
    raw_page = RawPage(
        source_name="unit_test",
        source_url="https://example.test",
        draw_date="2024-01-20",
        raw_html="<html></html>",
        raw_text="plain text",
        checksum="abc123",
        parser_version="v1",
        status="scraped",
    )

    sqlite_session.add_all([feature_snapshot, model_run, raw_page])
    sqlite_session.commit()

    stored_feature = sqlite_session.query(FeatureSnapshot).one()
    stored_run = sqlite_session.query(ModelRun).one()

    assert json.loads(stored_feature.feature_json) == feature_payload
    assert json.loads(stored_run.params_json) == params_payload
    assert json.loads(stored_run.metrics_json) == metrics_payload


def test_prediction_model_run_foreign_key_is_optional_and_enforced(sqlite_session) -> None:
    sqlite_session.execute(
        text(
            "INSERT INTO predictions "
            "(prediction_date, target_type, candidate_number, score, rank, model_run_id, created_at) "
            "VALUES ('2024-01-21', 'db_2cang', '05', 0.2, 1, NULL, CURRENT_TIMESTAMP)"
        )
    )
    sqlite_session.commit()

    with pytest.raises(IntegrityError):
        sqlite_session.execute(
            text(
                "INSERT INTO predictions "
                "(prediction_date, target_type, candidate_number, score, rank, model_run_id, created_at) "
                "VALUES ('2024-01-21', 'db_2cang', '06', 0.1, 2, 999, CURRENT_TIMESTAMP)"
            )
        )
