"""Pure transforms for XSMB loto target extraction and labels."""

from __future__ import annotations

from collections import Counter
from typing import Any

from xsmb.config import (
    DB_3CANG_NUMBERS,
    LOTO_2D_NUMBERS,
    PRIZE_SPECS,
    PRIZE_TIERS,
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
    TARGET_LOTO_2D_ALL_PRIZES,
)
from xsmb.processing.normalize import normalize_number
from xsmb.processing.validate import validate_draw_results


def extract_tail_digits(number: str, digits: int) -> str:
    """Extract the final digits from a lottery number using string slicing."""
    if not isinstance(digits, int):
        raise TypeError("digits must be an integer")
    if digits <= 0:
        raise ValueError("digits must be positive")
    if not isinstance(number, str):
        raise TypeError(f"Lottery numbers must be strings, got {type(number).__name__}")

    normalized = number.strip()
    if not normalized.isdigit():
        raise ValueError(f"Lottery number must contain only digits: {number!r}")
    if len(normalized) < digits:
        raise ValueError(
            f"Cannot extract {digits} digits from {normalized!r}; "
            f"only {len(normalized)} digits available"
        )
    return normalized[-digits:]


def candidate_space(target_type: str) -> list[str]:
    """Return the complete candidate number space for a supported target type."""
    if target_type in {TARGET_LOTO_2D_ALL_PRIZES, TARGET_DB_2CANG}:
        return list(LOTO_2D_NUMBERS)
    if target_type == TARGET_DB_3CANG:
        return list(DB_3CANG_NUMBERS)
    raise ValueError(f"Unsupported target_type: {target_type!r}")


def extract_loto_2d_all_prizes(rows: list[dict[str, Any]]) -> list[dict[str, Any]]:
    """Extract 27 two-digit loto entries from all XSMB prize rows."""
    validate_draw_results(rows)
    sorted_rows = sorted(
        rows, key=lambda row: (PRIZE_TIERS.index(row["prize_tier"]), row["prize_index"])
    )
    entries: list[dict[str, Any]] = []
    for row in sorted_rows:
        prize_tier = row["prize_tier"]
        winning_number = normalize_number(
            row["winning_number"], PRIZE_SPECS[prize_tier]["length"]
        )
        entries.append(
            {
                "draw_date": row["draw_date"],
                "prize_tier": prize_tier,
                "prize_index": row["prize_index"],
                "loto_number": extract_tail_digits(winning_number, 2),
            }
        )
    return entries


def extract_db_2cang(rows: list[dict[str, Any]]) -> str:
    """Extract the two-digit target from the special prize only."""
    special_number = _special_prize_number(rows)
    return extract_tail_digits(special_number, 2)


def extract_db_3cang(rows: list[dict[str, Any]]) -> str:
    """Extract the three-digit target from the special prize only."""
    special_number = _special_prize_number(rows)
    return extract_tail_digits(special_number, 3)


def build_target_hits(rows: list[dict[str, Any]], target_type: str) -> dict[str, int]:
    """Build hit counts for every candidate in a target type's candidate space."""
    hits = {candidate: 0 for candidate in candidate_space(target_type)}

    if target_type == TARGET_LOTO_2D_ALL_PRIZES:
        loto_numbers = [
            entry["loto_number"] for entry in extract_loto_2d_all_prizes(rows)
        ]
        hits.update(Counter(loto_numbers))
        return hits

    if target_type == TARGET_DB_2CANG:
        hits[extract_db_2cang(rows)] = 1
        return hits

    if target_type == TARGET_DB_3CANG:
        hits[extract_db_3cang(rows)] = 1
        return hits

    raise ValueError(f"Unsupported target_type: {target_type!r}")


def build_daily_training_labels(
    rows: list[dict[str, Any]], target_type: str
) -> list[dict[str, Any]]:
    """Build daily binary training labels for one complete XSMB draw."""
    validate_draw_results(rows)
    draw_date = rows[0]["draw_date"]
    hits = build_target_hits(rows, target_type)
    return [
        {
            "draw_date": draw_date,
            "target_type": target_type,
            "candidate_number": candidate,
            "label": 1 if hit_count > 0 else 0,
            "hit_count": hit_count,
        }
        for candidate, hit_count in hits.items()
    ]


def _special_prize_number(rows: list[dict[str, Any]]) -> str:
    validate_draw_results(rows)
    special_rows = [
        row
        for row in rows
        if row["prize_tier"] == "special" and row["prize_index"] == 0
    ]
    if len(special_rows) != 1:
        raise ValueError("Draw must contain exactly one special prize at index 0")
    return normalize_number(special_rows[0]["winning_number"], 5)
