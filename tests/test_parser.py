"""Tests for XSMB HTML parsing."""

from __future__ import annotations

from pathlib import Path

import pytest

from xsmb.config import PRIZE_SPECS, PRIZE_TIERS
from xsmb.processing.validate import validate_draw_results
from xsmb.scraping.parser import ParseError, parse_xsmb_result_html

FIXTURE_PATH = Path(__file__).parent / "fixtures" / "xsmb_sample_result.html"


@pytest.fixture
def fixture_html() -> str:
    """Load the static XSMB parser fixture."""
    return FIXTURE_PATH.read_text(encoding="utf-8")


def test_parser_reads_fixture_and_returns_27_rows(fixture_html: str) -> None:
    rows = parse_xsmb_result_html(fixture_html, "2024-01-15")

    assert len(rows) == 27
    assert rows[0] == {
        "draw_date": "2024-01-15",
        "prize_tier": "special",
        "prize_index": 0,
        "winning_number": "45008",
    }


def test_parser_preserves_leading_zeros(fixture_html: str) -> None:
    rows = parse_xsmb_result_html(fixture_html, "2024-01-15")

    assert any(row["winning_number"] == "007" for row in rows)
    assert any(row["winning_number"] == "05" for row in rows)
    assert all(isinstance(row["winning_number"], str) for row in rows)


def test_parser_maps_all_prize_tiers_to_phase_1_names(fixture_html: str) -> None:
    rows = parse_xsmb_result_html(fixture_html, "2024-01-15")
    counts = {tier: 0 for tier in PRIZE_TIERS}

    for row in rows:
        counts[row["prize_tier"]] += 1

    assert counts == {tier: PRIZE_SPECS[tier]["count"] for tier in PRIZE_TIERS}
    assert sorted({row["prize_index"] for row in rows if row["prize_tier"] == "third"}) == [
        0,
        1,
        2,
        3,
        4,
        5,
    ]


def test_parser_output_passes_validate_draw_results(fixture_html: str) -> None:
    rows = parse_xsmb_result_html(fixture_html, "2024-01-15")

    validate_draw_results(rows)


def test_parser_fails_on_missing_special_prize(fixture_html: str) -> None:
    html = fixture_html.replace('data-prize-tier="special"', 'data-prize-tier="missing"')

    with pytest.raises(ParseError, match="special"):
        parse_xsmb_result_html(html, "2024-01-15")


def test_parser_fails_on_wrong_prize_count(fixture_html: str) -> None:
    html = fixture_html.replace(
        '<span data-winning-number="67">67</span>',
        "",
        1,
    )

    with pytest.raises(ParseError, match="seventh"):
        parse_xsmb_result_html(html, "2024-01-15")


def test_parser_fails_on_wrong_number_length(fixture_html: str) -> None:
    html = fixture_html.replace('data-winning-number="45008"', 'data-winning-number="5008"')

    with pytest.raises(ParseError, match="special"):
        parse_xsmb_result_html(html, "2024-01-15")


def test_parser_fails_on_duplicate_or_malformed_sections(fixture_html: str) -> None:
    duplicate_special = """
      <section data-prize-tier="special">
        <span data-winning-number="99999">99999</span>
      </section>
    """
    html = fixture_html.replace("</main>", f"{duplicate_special}</main>")

    with pytest.raises(ParseError, match="Duplicate"):
        parse_xsmb_result_html(html, "2024-01-15")
