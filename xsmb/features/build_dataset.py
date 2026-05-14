"""Leakage-safe feature dataset builder for XSMB target history rows."""

from __future__ import annotations

from typing import Any

import pandas as pd

from xsmb.features.frequency_features import (
    FREQUENCY_WINDOWS,
    compute_frequency_features,
    sum_prior_hit_counts,
)
from xsmb.features.gap_features import compute_gap_features
from xsmb.features.rolling_features import compute_rolling_hit_rate_features
from xsmb.processing.transform import candidate_space

REQUIRED_COLUMNS: set[str] = {
    "draw_date",
    "target_type",
    "candidate_number",
    "label",
    "hit_count",
}

FEATURE_COLUMNS: list[str] = [
    "freq_7",
    "freq_14",
    "freq_30",
    "freq_60",
    "freq_90",
    "freq_180",
    "hit_count_sum_30",
    "current_gap",
    "days_since_last_seen",
    "max_gap_before_target",
    "avg_gap_before_target",
    "rolling_hit_rate_30",
    "rolling_hit_rate_90",
]

OUTPUT_COLUMNS: list[str] = [
    "target_date",
    "target_type",
    "candidate_number",
    "label",
    "hit_count",
    *FEATURE_COLUMNS,
]


def build_feature_dataset(
    history_df: pd.DataFrame,
    target_type: str,
    start_date: Any = None,
    end_date: Any = None,
    min_history_days: int = 30,
) -> pd.DataFrame:
    """Build leakage-safe feature rows for one explicit target type.

    All features for target date `T` are computed only from rows where
    `draw_date < T`. Date ordering is based on available draw dates for the
    requested target type, not calendar continuity.
    """
    if min_history_days < 0:
        raise ValueError("min_history_days must be non-negative")

    candidate_space(target_type)
    _validate_required_columns(history_df)

    df = _prepare_history(history_df, target_type)
    if df.empty:
        return pd.DataFrame(columns=OUTPUT_COLUMNS)

    start_dt = _optional_timestamp(start_date)
    end_dt = _optional_timestamp(end_date)
    draw_dates = list(pd.Series(df["_draw_date_dt"].unique()).sort_values())
    records: list[dict[str, Any]] = []

    for target_dt in draw_dates:
        if start_dt is not None and target_dt < start_dt:
            continue
        if end_dt is not None and target_dt > end_dt:
            continue

        prior_draw_dates = [draw_date for draw_date in draw_dates if draw_date < target_dt]
        if len(prior_draw_dates) < min_history_days:
            continue

        current_rows = df[df["_draw_date_dt"] == target_dt].sort_values(
            "candidate_number", kind="mergesort"
        )
        for row in current_rows.itertuples(index=False):
            candidate_number = row.candidate_number
            feature_row = {
                "target_date": target_dt.date().isoformat(),
                "target_type": target_type,
                "candidate_number": candidate_number,
                "label": int(row.label),
                "hit_count": int(row.hit_count),
            }
            feature_row.update(
                compute_frequency_features(
                    df, candidate_number, prior_draw_dates, FREQUENCY_WINDOWS
                )
            )
            feature_row["hit_count_sum_30"] = sum_prior_hit_counts(
                df, candidate_number, prior_draw_dates, window=30
            )
            feature_row.update(
                compute_gap_features(df, candidate_number, prior_draw_dates)
            )
            feature_row.update(
                compute_rolling_hit_rate_features(df, candidate_number, prior_draw_dates)
            )
            records.append(feature_row)

    return pd.DataFrame(records, columns=OUTPUT_COLUMNS)


def _validate_required_columns(history_df: pd.DataFrame) -> None:
    missing_columns = sorted(REQUIRED_COLUMNS - set(history_df.columns))
    if missing_columns:
        raise ValueError(f"history_df is missing required columns: {missing_columns}")


def _prepare_history(history_df: pd.DataFrame, target_type: str) -> pd.DataFrame:
    df = history_df.copy(deep=True)
    df = df[df["target_type"] == target_type].copy()
    if df.empty:
        return df.assign(_draw_date_dt=pd.Series(dtype="datetime64[ns]"))

    df["candidate_number"] = df["candidate_number"].astype(str)
    df["_draw_date_dt"] = pd.to_datetime(df["draw_date"], errors="raise")
    df["label"] = df["label"].astype(int)
    df["hit_count"] = df["hit_count"].astype(int)

    return (
        df.groupby(
            ["_draw_date_dt", "target_type", "candidate_number"],
            as_index=False,
            sort=False,
        )
        .agg(label=("label", "max"), hit_count=("hit_count", "sum"))
        .sort_values(["_draw_date_dt", "candidate_number"], kind="mergesort")
        .reset_index(drop=True)
    )


def _optional_timestamp(value: Any) -> pd.Timestamp | None:
    if value is None:
        return None
    return pd.Timestamp(value)
