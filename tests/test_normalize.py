"""Tests for XSMB number normalization."""

from __future__ import annotations

import pytest

from xsmb.processing.normalize import normalize_number
from xsmb.processing.transform import extract_tail_digits


def test_normalize_number_preserves_leading_zeros() -> None:
    assert normalize_number("00512", expected_length=5) == "00512"
    assert normalize_number("00", expected_length=2) == "00"
    assert normalize_number("09", expected_length=2) == "09"


def test_normalize_number_requires_string() -> None:
    with pytest.raises(TypeError, match="must be strings"):
        normalize_number(5, expected_length=2)  # type: ignore[arg-type]


def test_normalize_number_rejects_wrong_length() -> None:
    with pytest.raises(ValueError, match="must be 5 digits"):
        normalize_number("1234", expected_length=5)


def test_normalize_number_rejects_non_digits() -> None:
    with pytest.raises(ValueError, match="only digits"):
        normalize_number("45a78", expected_length=5)


def test_extract_tail_digits_preserves_zero_padding() -> None:
    assert extract_tail_digits("10005", 2) == "05"
    assert extract_tail_digits("00100", 2) == "00"
    assert extract_tail_digits("45008", 3) == "008"
