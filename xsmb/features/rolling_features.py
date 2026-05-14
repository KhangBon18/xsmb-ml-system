"""Rolling-rate feature helpers for target history rows."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd

from xsmb.features.frequency_features import count_prior_labels

ROLLING_RATE_WINDOWS: tuple[int, ...] = (30, 90)


def compute_rolling_hit_rate_features(
    history_df: pd.DataFrame,
    candidate_number: str,
    prior_draw_dates: Sequence[pd.Timestamp],
    windows: Sequence[int] = ROLLING_RATE_WINDOWS,
) -> dict[str, float]:
    """Compute rolling hit rates for one candidate using prior dates only."""
    return {
        f"rolling_hit_rate_{window}": rolling_hit_rate(
            history_df, candidate_number, prior_draw_dates, window
        )
        for window in windows
    }


def rolling_hit_rate(
    history_df: pd.DataFrame,
    candidate_number: str,
    prior_draw_dates: Sequence[pd.Timestamp],
    window: int,
) -> float:
    """Return frequency divided by available prior dates in the latest window."""
    if window <= 0:
        raise ValueError("window must be positive")

    window_dates = list(prior_draw_dates)[-window:]
    if not window_dates:
        return 0.0

    return count_prior_labels(
        history_df, candidate_number, prior_draw_dates, window
    ) / len(window_dates)
