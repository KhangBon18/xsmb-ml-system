"""Normalization helpers for XSMB lottery numbers."""

from __future__ import annotations


def normalize_number(value: str, expected_length: int) -> str:
    """Return a cleaned lottery number string with its leading zeros preserved.

    Args:
        value: Raw lottery number. It must already be a string so leading zeros
            cannot be lost before this function is called.
        expected_length: Exact number of digits required for the value.

    Raises:
        TypeError: If value is not a string or expected_length is not an int.
        ValueError: If the normalized value is non-digit or has the wrong length.
    """
    if not isinstance(value, str):
        raise TypeError(f"Lottery numbers must be strings, got {type(value).__name__}")
    if not isinstance(expected_length, int):
        raise TypeError("expected_length must be an integer")
    if expected_length <= 0:
        raise ValueError("expected_length must be positive")

    normalized = value.strip()
    if not normalized.isdigit():
        raise ValueError(f"Lottery number must contain only digits: {value!r}")
    if len(normalized) != expected_length:
        raise ValueError(
            f"Lottery number {normalized!r} must be {expected_length} digits, "
            f"got {len(normalized)}"
        )
    return normalized
