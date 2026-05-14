"""Deterministic baseline ranking models for XSMB targets."""

from __future__ import annotations

import pandas as pd

SUPPORTED_BASELINES: set[str] = {
    "random_uniform",
    "frequency_30",
    "frequency_90",
    "gap_rank",
}

BASE_REQUIRED_COLUMNS: set[str] = {
    "target_date",
    "target_type",
    "candidate_number",
    "label",
    "hit_count",
}


def score_baseline_candidates(feature_df: pd.DataFrame, model_name: str) -> pd.DataFrame:
    """Score and rank candidate rows with a deterministic baseline model."""
    if model_name not in SUPPORTED_BASELINES:
        raise ValueError(f"Unsupported baseline model_name: {model_name!r}")
    _validate_required_columns(feature_df, model_name)

    df = feature_df.copy(deep=True)
    if df.empty:
        return _empty_predictions()

    df["candidate_number"] = df["candidate_number"].astype(str)
    df["score"] = _compute_scores(df, model_name)
    df["probability"] = _compute_probabilities(df, model_name).clip(0.0, 1.0)
    df["model_name"] = model_name

    ranked = (
        df.sort_values(
            ["target_date", "score", "candidate_number"],
            ascending=[True, False, True],
            kind="mergesort",
        )
        .reset_index(drop=True)
    )
    ranked["rank"] = ranked.groupby("target_date").cumcount() + 1

    return ranked[
        [
            "target_date",
            "target_type",
            "candidate_number",
            "score",
            "probability",
            "rank",
            "label",
            "hit_count",
            "model_name",
        ]
    ].sort_values(["target_date", "rank"], kind="mergesort", ignore_index=True)


def _validate_required_columns(feature_df: pd.DataFrame, model_name: str) -> None:
    required_columns = set(BASE_REQUIRED_COLUMNS)
    if model_name == "frequency_30":
        if "rolling_hit_rate_30" not in feature_df.columns:
            required_columns.add("freq_30")
    elif model_name == "frequency_90":
        if "rolling_hit_rate_90" not in feature_df.columns:
            required_columns.add("freq_90")
    elif model_name == "gap_rank":
        required_columns.add("current_gap")

    missing_columns = sorted(required_columns - set(feature_df.columns))
    if missing_columns:
        raise ValueError(f"feature_df is missing required columns: {missing_columns}")


def _compute_scores(df: pd.DataFrame, model_name: str) -> pd.Series:
    if model_name == "random_uniform":
        return pd.Series(1.0, index=df.index, dtype="float64")
    if model_name == "frequency_30":
        return _frequency_probability(df, window=30)
    if model_name == "frequency_90":
        return _frequency_probability(df, window=90)
    if model_name == "gap_rank":
        return 1.0 / (df["current_gap"].astype(float) + 1.0)
    raise ValueError(f"Unsupported baseline model_name: {model_name!r}")


def _compute_probabilities(df: pd.DataFrame, model_name: str) -> pd.Series:
    if model_name == "random_uniform":
        candidate_counts = df.groupby("target_date")["candidate_number"].transform("count")
        return 1.0 / candidate_counts.astype(float)
    return _compute_scores(df, model_name)


def _frequency_probability(df: pd.DataFrame, window: int) -> pd.Series:
    rolling_column = f"rolling_hit_rate_{window}"
    frequency_column = f"freq_{window}"
    if rolling_column in df.columns:
        return df[rolling_column].astype(float)
    return (df[frequency_column].astype(float) / float(window)).clip(upper=1.0)


def _empty_predictions() -> pd.DataFrame:
    return pd.DataFrame(
        columns=[
            "target_date",
            "target_type",
            "candidate_number",
            "score",
            "probability",
            "rank",
            "label",
            "hit_count",
            "model_name",
        ]
    )
