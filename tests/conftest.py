"""Shared test fixtures for Phase 1 domain processing."""

from __future__ import annotations

import pytest


@pytest.fixture
def sample_draw_rows() -> list[dict[str, object]]:
    """Return one complete valid XSMB draw with repeated two-digit tails."""
    draw_date = "2024-01-15"
    rows_by_tier = {
        "special": ["45678"],
        "first": ["12345"],
        "second": ["67890", "11223"],
        "third": ["33445", "55667", "78901", "23456", "78012", "90123"],
        "fourth": ["1234", "5678", "9012", "3456"],
        "fifth": ["7890", "1234", "5678", "9012", "3456", "7890"],
        "sixth": ["123", "456", "789"],
        "seventh": ["01", "23", "45", "67"],
    }

    rows: list[dict[str, object]] = []
    for prize_tier, winning_numbers in rows_by_tier.items():
        for prize_index, winning_number in enumerate(winning_numbers):
            rows.append(
                {
                    "draw_date": draw_date,
                    "prize_tier": prize_tier,
                    "prize_index": prize_index,
                    "winning_number": winning_number,
                }
            )
    return rows
