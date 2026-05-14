"""Tests for Phase 1 XSMB target extraction and label building."""

from __future__ import annotations

import pytest

from xsmb.config import (
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
    TARGET_LOTO_2D_ALL_PRIZES,
)
from xsmb.processing.transform import (
    build_daily_training_labels,
    build_target_hits,
    candidate_space,
    extract_db_2cang,
    extract_db_3cang,
    extract_loto_2d_all_prizes,
    extract_tail_digits,
)


def test_extract_tail_digits_examples() -> None:
    assert extract_tail_digits("45678", 2) == "78"
    assert extract_tail_digits("105", 2) == "05"
    assert extract_tail_digits("02", 2) == "02"
    assert extract_tail_digits("45678", 3) == "678"


def test_candidate_space_sizes_and_zero_padding() -> None:
    loto_candidates = candidate_space(TARGET_LOTO_2D_ALL_PRIZES)
    db_2cang_candidates = candidate_space(TARGET_DB_2CANG)
    db_3cang_candidates = candidate_space(TARGET_DB_3CANG)

    assert len(loto_candidates) == 100
    assert len(db_2cang_candidates) == 100
    assert len(db_3cang_candidates) == 1000
    assert loto_candidates[:10] == ["00", "01", "02", "03", "04", "05", "06", "07", "08", "09"]
    assert db_3cang_candidates[:10] == [
        "000",
        "001",
        "002",
        "003",
        "004",
        "005",
        "006",
        "007",
        "008",
        "009",
    ]
    assert all(isinstance(candidate, str) for candidate in db_3cang_candidates)


def test_extract_loto_2d_all_prizes_returns_27_entries(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    entries = extract_loto_2d_all_prizes(sample_draw_rows)

    assert len(entries) == 27
    assert entries[0]["loto_number"] == "78"
    assert entries[-1]["loto_number"] == "67"
    assert all(len(entry["loto_number"]) == 2 for entry in entries)


def test_extract_db_targets_use_special_prize_only(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    rows = [dict(row) for row in sample_draw_rows]
    rows[0]["winning_number"] = "00512"
    rows[1]["winning_number"] = "99999"

    assert extract_db_2cang(rows) == "12"
    assert extract_db_3cang(rows) == "512"


def test_loto_2d_hit_count_allows_multiple_hits(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    hits = build_target_hits(sample_draw_rows, TARGET_LOTO_2D_ALL_PRIZES)

    assert hits["78"] == 3
    assert hits["90"] == 3
    assert hits["00"] == 0


@pytest.mark.parametrize(
    ("target_type", "expected_rows", "expected_positive"),
    [
        (TARGET_LOTO_2D_ALL_PRIZES, 100, 10),
        (TARGET_DB_2CANG, 100, 1),
        (TARGET_DB_3CANG, 1000, 1),
    ],
)
def test_build_daily_training_labels_row_counts_and_positive_counts(
    sample_draw_rows: list[dict[str, object]],
    target_type: str,
    expected_rows: int,
    expected_positive: int,
) -> None:
    labels = build_daily_training_labels(sample_draw_rows, target_type)

    assert len(labels) == expected_rows
    assert sum(row["label"] for row in labels) == expected_positive
    assert all(row["target_type"] == target_type for row in labels)
    assert all(row["draw_date"] == "2024-01-15" for row in labels)


def test_build_daily_training_labels_includes_required_fields(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    labels = build_daily_training_labels(sample_draw_rows, TARGET_DB_3CANG)
    winning_row = next(row for row in labels if row["label"] == 1)

    assert set(winning_row) == {
        "draw_date",
        "target_type",
        "candidate_number",
        "label",
        "hit_count",
    }
    assert winning_row["candidate_number"] == "678"
    assert winning_row["hit_count"] == 1


def test_db_2cang_labels_do_not_use_other_prize_tails(
    sample_draw_rows: list[dict[str, object]]
) -> None:
    rows = [dict(row) for row in sample_draw_rows]
    rows[0]["winning_number"] = "45678"
    rows[1]["winning_number"] = "12345"
    labels = build_daily_training_labels(rows, TARGET_DB_2CANG)

    assert next(row for row in labels if row["candidate_number"] == "78")["label"] == 1
    assert next(row for row in labels if row["candidate_number"] == "45")["label"] == 0
