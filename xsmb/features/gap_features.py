"""Draw-index gap feature helpers for target history rows."""

from __future__ import annotations

from collections.abc import Sequence

import pandas as pd


def compute_gap_features(
    history_df: pd.DataFrame,
    candidate_number: str,
    prior_draw_dates: Sequence[pd.Timestamp],
) -> dict[str, float]:
    """Compute leakage-safe gap features for one candidate before a target date."""
    prior_dates = list(prior_draw_dates)
    prior_count = len(prior_dates)
    hit_indices = _hit_indices(history_df, candidate_number, prior_dates)

    if not hit_indices:
        current_gap = prior_count
        return {
            "current_gap": current_gap,
            "days_since_last_seen": current_gap,
            "max_gap_before_target": current_gap,
            "avg_gap_before_target": float(current_gap),
        }

    current_gap = prior_count - 1 - hit_indices[-1]
    if len(hit_indices) == 1:
        max_gap = current_gap
        avg_gap = float(current_gap)
    else:
        between_hit_gaps = [
            current_index - previous_index - 1
            for previous_index, current_index in zip(hit_indices, hit_indices[1:])
        ]
        max_gap = max(between_hit_gaps)
        avg_gap = float(sum(between_hit_gaps) / len(between_hit_gaps))

    return {
        "current_gap": current_gap,
        "days_since_last_seen": current_gap,
        "max_gap_before_target": max_gap,
        "avg_gap_before_target": avg_gap,
    }


def _hit_indices(
    history_df: pd.DataFrame,
    candidate_number: str,
    prior_draw_dates: Sequence[pd.Timestamp],
) -> list[int]:
    hit_dates = set(
        history_df[
            (history_df["candidate_number"] == candidate_number)
            & (history_df["label"] == 1)
            & (history_df["_draw_date_dt"].isin(prior_draw_dates))
        ]["_draw_date_dt"]
    )
    return [index for index, draw_date in enumerate(prior_draw_dates) if draw_date in hit_dates]
