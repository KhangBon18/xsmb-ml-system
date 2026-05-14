"""Evaluation metrics for probability-ranking predictions."""

from __future__ import annotations

from collections.abc import Iterable

import numpy as np
import pandas as pd

PREDICTION_REQUIRED_COLUMNS: set[str] = {
    "target_date",
    "target_type",
    "candidate_number",
    "probability",
    "rank",
    "label",
    "hit_count",
}


def brier_score(y_true: Iterable[float], y_prob: Iterable[float]) -> float:
    """Return mean squared error between binary labels and probabilities."""
    y_true_array = np.asarray(list(y_true), dtype=float)
    y_prob_array = np.asarray(list(y_prob), dtype=float)
    _validate_same_length(y_true_array, y_prob_array)
    return float(np.mean((y_true_array - y_prob_array) ** 2))


def log_loss(y_true: Iterable[float], y_prob: Iterable[float], eps: float = 1e-15) -> float:
    """Return binary log loss with probability clipping."""
    y_true_array = np.asarray(list(y_true), dtype=float)
    y_prob_array = np.asarray(list(y_prob), dtype=float)
    _validate_same_length(y_true_array, y_prob_array)
    clipped = np.clip(y_prob_array, eps, 1.0 - eps)
    return float(
        -np.mean(y_true_array * np.log(clipped) + (1.0 - y_true_array) * np.log(1.0 - clipped))
    )


def precision_at_k(predictions_df: pd.DataFrame, k: int) -> float:
    """Average per-date precision among rows with rank <= k."""
    return _average_per_date(predictions_df, k, lambda top_rows, _date_rows: top_rows["label"].mean())


def hit_rate_at_k(predictions_df: pd.DataFrame, k: int) -> float:
    """Average per-date indicator for at least one positive row in top-k."""
    return _average_per_date(
        predictions_df,
        k,
        lambda top_rows, _date_rows: float((top_rows["label"] == 1).any()),
    )


def avg_hits_at_k(predictions_df: pd.DataFrame, k: int) -> float:
    """Average per-date sum of hit_count in top-k rows."""
    return _average_per_date(predictions_df, k, lambda top_rows, _date_rows: top_rows["hit_count"].sum())


def recall_at_k(predictions_df: pd.DataFrame, k: int) -> float:
    """Average per-date recall, skipping dates with no positive labels."""
    _validate_predictions_df(predictions_df)
    _validate_k(k)
    recalls: list[float] = []
    for _target_date, date_rows in predictions_df.groupby("target_date", sort=True):
        positives = float(date_rows["label"].sum())
        if positives <= 0:
            continue
        top_rows = date_rows[date_rows["rank"] <= k]
        recalls.append(float(top_rows["label"].sum() / positives))
    if not recalls:
        return 0.0
    return float(np.mean(recalls))


def calibration_by_bucket(predictions_df: pd.DataFrame, n_buckets: int = 10) -> pd.DataFrame:
    """Bucket probabilities over [0, 1] and report empirical hit rates."""
    _validate_predictions_df(predictions_df)
    if n_buckets <= 0:
        raise ValueError("n_buckets must be positive")

    df = predictions_df.copy(deep=True)
    probabilities = df["probability"].astype(float).clip(0.0, 1.0)
    df["_bucket"] = np.minimum((probabilities * n_buckets).astype(int), n_buckets - 1)
    grouped = (
        df.groupby("_bucket", sort=True)
        .agg(
            count=("label", "size"),
            avg_probability=("probability", "mean"),
            empirical_hit_rate=("label", "mean"),
        )
        .reset_index()
        .rename(columns={"_bucket": "bucket"})
    )
    return grouped[["bucket", "count", "avg_probability", "empirical_hit_rate"]]


def evaluate_predictions(
    predictions_df: pd.DataFrame, top_k_values: tuple[int, ...] = (5, 10, 20)
) -> dict[str, float | int]:
    """Return summary metrics for ranked prediction rows."""
    _validate_predictions_df(predictions_df)
    if predictions_df.empty:
        raise ValueError("predictions_df must not be empty")

    summary: dict[str, float | int] = {
        "brier_score": brier_score(predictions_df["label"], predictions_df["probability"]),
        "log_loss": log_loss(predictions_df["label"], predictions_df["probability"]),
        "row_count": int(len(predictions_df)),
        "date_count": int(predictions_df["target_date"].nunique()),
    }
    for k in top_k_values:
        _validate_k(k)
        summary[f"precision_at_{k}"] = precision_at_k(predictions_df, k)
        summary[f"hit_rate_at_{k}"] = hit_rate_at_k(predictions_df, k)
        summary[f"avg_hits_at_{k}"] = avg_hits_at_k(predictions_df, k)
        summary[f"recall_at_{k}"] = recall_at_k(predictions_df, k)
    return summary


def _average_per_date(predictions_df: pd.DataFrame, k: int, fn) -> float:  # type: ignore[no-untyped-def]
    _validate_predictions_df(predictions_df)
    _validate_k(k)
    values = []
    for _target_date, date_rows in predictions_df.groupby("target_date", sort=True):
        top_rows = date_rows[date_rows["rank"] <= k]
        if top_rows.empty:
            continue
        values.append(float(fn(top_rows, date_rows)))
    if not values:
        return 0.0
    return float(np.mean(values))


def _validate_predictions_df(predictions_df: pd.DataFrame) -> None:
    missing_columns = sorted(PREDICTION_REQUIRED_COLUMNS - set(predictions_df.columns))
    if missing_columns:
        raise ValueError(f"predictions_df is missing required columns: {missing_columns}")


def _validate_k(k: int) -> None:
    if not isinstance(k, int) or k <= 0:
        raise ValueError("k must be a positive integer")


def _validate_same_length(y_true: np.ndarray, y_prob: np.ndarray) -> None:
    if len(y_true) == 0:
        raise ValueError("inputs must not be empty")
    if len(y_true) != len(y_prob):
        raise ValueError("y_true and y_prob must have the same length")
