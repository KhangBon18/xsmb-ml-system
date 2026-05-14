"""Small Phase 3 ingestion bridge from raw HTML to database rows."""

from __future__ import annotations

import hashlib
from dataclasses import dataclass
from datetime import date

from bs4 import BeautifulSoup
from sqlalchemy.orm import Session

from xsmb.config import TARGET_TYPES
from xsmb.database.models import Draw, Prize, RawPage, Target
from xsmb.database.repository import (
    DrawRepository,
    PrizeRepository,
    RawPageRepository,
    TargetRepository,
)
from xsmb.scraping.parser import parse_xsmb_result_html
from xsmb.scraping.sources import get_default_xsmb_source


@dataclass(frozen=True)
class IngestionResult:
    """Rows produced by one idempotent HTML ingestion operation."""

    raw_page: RawPage
    draw: Draw
    prizes: list[Prize]
    targets_by_type: dict[str, list[Target]]


def ingest_xsmb_html(
    session: Session,
    html: str,
    draw_date: str | date,
    source_url: str,
    source_name: str,
    *,
    parser_version: str | None = None,
    generate_targets: bool = True,
    target_types: tuple[str, ...] = TARGET_TYPES,
) -> IngestionResult:
    """Parse and save one XSMB HTML page without committing the session."""
    draw_date_str = _coerce_draw_date(draw_date)
    parser_version = parser_version or get_default_xsmb_source().parser_version
    checksum = hashlib.sha256(html.encode("utf-8")).hexdigest()

    raw_page = RawPageRepository(session).insert(
        source_name=source_name,
        source_url=source_url,
        draw_date=draw_date_str,
        raw_html=html,
        raw_text=BeautifulSoup(html, "html.parser").get_text(" ", strip=True),
        checksum=checksum,
        parser_version=parser_version,
        status="parsed",
    )

    prize_rows = parse_xsmb_result_html(html, draw_date_str)
    draw = DrawRepository(session).create_or_get(
        draw_date=draw_date_str,
        source_name=source_name,
        status="parsed",
    )
    prizes = PrizeRepository(session).save_prizes(draw, prize_rows)

    targets_by_type: dict[str, list[Target]] = {}
    if generate_targets:
        target_repository = TargetRepository(session)
        for target_type in target_types:
            targets_by_type[target_type] = target_repository.generate_and_save_targets(
                draw, target_type
            )

    return IngestionResult(
        raw_page=raw_page,
        draw=draw,
        prizes=prizes,
        targets_by_type=targets_by_type,
    )


def _coerce_draw_date(value: str | date) -> str:
    if isinstance(value, date):
        return value.isoformat()
    if isinstance(value, str):
        return date.fromisoformat(value).isoformat()
    raise TypeError(f"draw_date must be str or date, got {type(value).__name__}")
