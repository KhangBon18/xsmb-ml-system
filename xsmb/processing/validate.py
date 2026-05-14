"""Validation for normalized XSMB draw result rows."""

from __future__ import annotations

from collections import Counter, defaultdict
from datetime import date
from typing import Any

from xsmb.config import PRIZE_SPECS, TOTAL_PRIZE_COUNT
from xsmb.processing.normalize import normalize_number

REQUIRED_DRAW_KEYS = frozenset(
    {"draw_date", "prize_tier", "prize_index", "winning_number"}
)


def validate_draw_results(rows: list[dict[str, Any]]) -> None:
    """Validate that rows represent exactly one complete XSMB draw.

    A valid draw contains exactly 27 prize rows, the expected count and digit
    length for each prize tier, string lottery numbers, one ISO draw date, and
    sequential 0-based prize indices per tier.

    Raises:
        ValueError: If the draw shape or values violate the XSMB data contract.
        TypeError: If rows or row fields have invalid types.
    """
    if not isinstance(rows, list):
        raise TypeError("rows must be a list of dictionaries")
    if len(rows) != TOTAL_PRIZE_COUNT:
        raise ValueError(
            f"XSMB draw must contain exactly {TOTAL_PRIZE_COUNT} prize rows, "
            f"got {len(rows)}"
        )

    draw_dates: set[str] = set()
    tier_counts: Counter[str] = Counter()
    tier_indices: dict[str, list[int]] = defaultdict(list)
    seen_tier_indices: set[tuple[str, int]] = set()

    for row_number, row in enumerate(rows, start=1):
        if not isinstance(row, dict):
            raise TypeError(f"Draw row {row_number} must be a dictionary")

        missing_keys = REQUIRED_DRAW_KEYS - row.keys()
        if missing_keys:
            raise ValueError(
                f"Draw row {row_number} is missing required keys: "
                f"{sorted(missing_keys)}"
            )

        draw_date = row["draw_date"]
        if not isinstance(draw_date, str):
            raise TypeError(f"draw_date must be a string in row {row_number}")
        try:
            date.fromisoformat(draw_date)
        except ValueError as exc:
            raise ValueError(
                f"draw_date must use ISO format YYYY-MM-DD: {draw_date!r}"
            ) from exc
        draw_dates.add(draw_date)

        prize_tier = row["prize_tier"]
        if not isinstance(prize_tier, str):
            raise TypeError(f"prize_tier must be a string in row {row_number}")
        if prize_tier not in PRIZE_SPECS:
            raise ValueError(f"Unknown prize_tier in row {row_number}: {prize_tier!r}")

        prize_index = row["prize_index"]
        if not isinstance(prize_index, int):
            raise TypeError(f"prize_index must be an integer in row {row_number}")
        if prize_index < 0:
            raise ValueError(f"prize_index must be non-negative in row {row_number}")

        tier_index = (prize_tier, prize_index)
        if tier_index in seen_tier_indices:
            raise ValueError(f"Duplicate prize tier/index: {tier_index!r}")
        seen_tier_indices.add(tier_index)

        expected_length = PRIZE_SPECS[prize_tier]["length"]
        normalize_number(row["winning_number"], expected_length)

        tier_counts[prize_tier] += 1
        tier_indices[prize_tier].append(prize_index)

    if len(draw_dates) != 1:
        raise ValueError(f"Rows must contain exactly one draw_date, got {draw_dates!r}")

    for prize_tier, spec in PRIZE_SPECS.items():
        actual_count = tier_counts[prize_tier]
        expected_count = spec["count"]
        if actual_count != expected_count:
            raise ValueError(
                f"Prize tier {prize_tier!r} must contain {expected_count} rows, "
                f"got {actual_count}"
            )

        expected_indices = list(range(expected_count))
        actual_indices = sorted(tier_indices[prize_tier])
        if actual_indices != expected_indices:
            raise ValueError(
                f"Prize tier {prize_tier!r} must use indices {expected_indices}, "
                f"got {actual_indices}"
            )
