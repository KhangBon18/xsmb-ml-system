"""Frequency feature helpers for target history rows."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

FREQUENCY_WINDOWS: tuple[int, ...] = (7, 14, 30, 60, 90, 180)


def compute_frequency_features(
    history_df: pd.DataFrame,
    candidate_number: str,
    prior_draw_dates: Sequence[pd.Timestamp],
    windows: Sequence[int] = FREQUENCY_WINDOWS,
) -> dict[str, int]:
    """Compute label-frequency windows for one candidate using prior dates only."""
    return {
        f"freq_{window}": count_prior_labels(
            history_df, candidate_number, prior_draw_dates, window
        )
        for window in windows
    }


def count_prior_labels(
    history_df: pd.DataFrame,
    candidate_number: str,
    prior_draw_dates: Sequence[pd.Timestamp],
    window: int,
) -> int:
    """Count positive-label draw days in the latest prior date window."""
    if window <= 0:
        raise ValueError("window must be positive")

    window_dates = list(prior_draw_dates)[-window:]
    if not window_dates:
        return 0

    rows = history_df[
        (history_df["candidate_number"] == candidate_number)
        & (history_df["_draw_date_dt"].isin(window_dates))
    ]
    return int(rows["label"].sum())


def sum_prior_hit_counts(
    history_df: pd.DataFrame,
    candidate_number: str,
    prior_draw_dates: Sequence[pd.Timestamp],
    window: int = 30,
) -> int:
    """Sum hit counts for one candidate in the latest prior date window."""
    if window <= 0:
        raise ValueError("window must be positive")

    window_dates = list(prior_draw_dates)[-window:]
    if not window_dates:
        return 0

    rows = history_df[
        (history_df["candidate_number"] == candidate_number)
        & (history_df["_draw_date_dt"].isin(window_dates))
    ]
    return int(rows["hit_count"].sum())
