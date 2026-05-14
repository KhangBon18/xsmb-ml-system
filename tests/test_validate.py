"""Tests for XSMB draw validation."""

from __future__ import annotations

import pytest

from xsmb.processing.validate import validate_draw_results


def test_validate_draw_results_accepts_complete_27_prize_draw(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    validate_draw_results(sample_draw_rows)


def test_validate_draw_results_rejects_wrong_total_count(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    with pytest.raises(ValueError, match="exactly 27"):
        validate_draw_results(sample_draw_rows[:-1])


def test_validate_draw_results_rejects_wrong_prize_count(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    rows = [
        row
        for row in sample_draw_rows
        if not (row["prize_tier"] == "seventh" and row["prize_index"] == 3)
    ]
    rows.append(
        {
            "draw_date": "2024-01-15",
            "prize_tier": "sixth",
            "prize_index": 3,
            "winning_number": "111",
        }
    )

    with pytest.raises(ValueError, match="must contain"):
        validate_draw_results(rows)


def test_validate_draw_results_rejects_wrong_length(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    rows = [dict(row) for row in sample_draw_rows]
    rows[0]["winning_number"] = "5678"

    with pytest.raises(ValueError, match="must be 5 digits"):
        validate_draw_results(rows)


def test_validate_draw_results_rejects_non_digit_number(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    rows = [dict(row) for row in sample_draw_rows]
    rows[0]["winning_number"] = "45a78"

    with pytest.raises(ValueError, match="only digits"):
        validate_draw_results(rows)
