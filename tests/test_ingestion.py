"""Tests for Phase 3 XSMB HTML ingestion."""

from __future__ import annotations

from pathlib import Path

import pytest

from xsmb.config import (
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
    TARGET_LOTO_2D_ALL_PRIZES,
)
from xsmb.database.connection import create_engine_from_url, create_session_factory
from xsmb.database.models import Draw, Prize, RawPage, Target, drop_db, init_db
from xsmb.scraping.ingest import ingest_xsmb_html

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "xsmb_sample_result.html"


@pytest.fixture
def ingestion_session(tmp_path: Path):
    """Create a temporary SQLite session for ingestion tests."""
    engine = create_engine_from_url(f"sqlite:///{tmp_path / 'ingestion.sqlite3'}")
    init_db(engine)
    session_factory = create_session_factory(engine)

    with session_factory() as session:
        yield session

    drop_db(engine)
    engine.dispose()


@pytest.fixture
def fixture_html() -> str:
    """Load the XSMB ingestion fixture."""
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_ingestion_saves_raw_page_draw_and_27_prizes(
    ingestion_session,
    fixture_html: str,
) -> None:
    result = ingest_xsmb_html(
        ingestion_session,
        fixture_html,
        "2024-01-15",
        "https://example.test/xsmb-15-01-2024.html",
        "unit_source",
        generate_targets=False,
    )

    assert result.raw_page.id is not None
    assert result.draw.draw_date == "2024-01-15"
    assert len(result.prizes) == 27
    assert ingestion_session.query(RawPage).count() == 1
    assert ingestion_session.query(Draw).count() == 1
    assert ingestion_session.query(Prize).count() == 27
    assert ingestion_session.query(Prize).filter_by(winning_number="007").count() == 1
    assert ingestion_session.query(Prize).filter_by(winning_number="05").count() == 1


def test_ingestion_generates_all_target_types(
    ingestion_session,
    fixture_html: str,
) -> None:
    result = ingest_xsmb_html(
        ingestion_session,
        fixture_html,
        "2024-01-15",
        "https://example.test/xsmb-15-01-2024.html",
        "unit_source",
    )

    assert len(result.targets_by_type[TARGET_LOTO_2D_ALL_PRIZES]) == 100
    assert len(result.targets_by_type[TARGET_DB_2CANG]) == 100
    assert len(result.targets_by_type[TARGET_DB_3CANG]) == 1000
    assert ingestion_session.query(Target).count() == 1200

    db_2_winner = (
        ingestion_session.query(Target)
        .filter_by(target_type=TARGET_DB_2CANG, candidate_number="08")
        .one()
    )
    db_3_winner = (
        ingestion_session.query(Target)
        .filter_by(target_type=TARGET_DB_3CANG, candidate_number="008")
        .one()
    )
    db_2_other_prize_tail = (
        ingestion_session.query(Target)
        .filter_by(target_type=TARGET_DB_2CANG, candidate_number="45")
        .one()
    )

    assert db_2_winner.label == 1
    assert db_3_winner.label == 1
    assert db_2_other_prize_tail.label == 0


def test_ingestion_is_idempotent_for_same_date_and_html(
    ingestion_session,
    fixture_html: str,
) -> None:
    first = ingest_xsmb_html(
        ingestion_session,
        fixture_html,
        "2024-01-15",
        "https://example.test/xsmb-15-01-2024.html",
        "unit_source",
    )
    second = ingest_xsmb_html(
        ingestion_session,
        fixture_html,
        "2024-01-15",
        "https://example.test/xsmb-15-01-2024.html",
        "unit_source",
    )

    assert second.raw_page.id == first.raw_page.id
    assert second.draw.id == first.draw.id
    assert [prize.id for prize in second.prizes] == [prize.id for prize in first.prizes]
    assert ingestion_session.query(RawPage).count() == 1
    assert ingestion_session.query(Draw).count() == 1
    assert ingestion_session.query(Prize).count() == 27
    assert ingestion_session.query(Target).count() == 1200
