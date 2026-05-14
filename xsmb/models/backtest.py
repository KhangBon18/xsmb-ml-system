"""Walk-forward backtesting for deterministic baseline models."""

from __future__ import annotations

from typing import Any

import pandas as pd

from xsmb.features.build_dataset import build_feature_dataset
from xsmb.models.baseline import SUPPORTED_BASELINES, score_baseline_candidates
from xsmb.models.evaluate import calibration_by_bucket, evaluate_predictions
from xsmb.processing.transform import candidate_space


def run_walk_forward_backtest(
    history_df: pd.DataFrame,
    target_type: str,
    model_name: str,
    start_date: Any = None,
    end_date: Any = None,
    min_history_days: int = 30,
    top_k_values: tuple[int, ...] = (5, 10, 20),
) -> dict[str, Any]:
    """Run a time-based baseline backtest using leakage-safe feature rows."""
    candidate_space(target_type)
    if model_name not in SUPPORTED_BASELINES:
        raise ValueError(f"Unsupported baseline model_name: {model_name!r}")

    feature_df = build_feature_dataset(
        history_df,
        target_type=target_type,
        start_date=start_date,
        end_date=end_date,
        min_history_days=min_history_days,
    )
    predictions_df = score_baseline_candidates(feature_df, model_name)
    summary = evaluate_predictions(predictions_df, top_k_values=top_k_values)
    calibration = calibration_by_bucket(predictions_df)

    return {
        "target_type": target_type,
        "model_name": model_name,
        "start_date": _optional_iso_date(start_date),
        "end_date": _optional_iso_date(end_date),
        "min_history_days": min_history_days,
        "predictions": predictions_df,
        "summary": summary,
        "calibration": calibration,
    }


def summarize_backtest_result(result: dict[str, Any]) -> dict[str, Any]:
    """Return metadata plus summary metrics without large DataFrame payloads."""
    return {
        "target_type": result["target_type"],
        "model_name": result["model_name"],
        "start_date": result["start_date"],
        "end_date": result["end_date"],
        "min_history_days": result["min_history_days"],
        **result["summary"],
    }


def predictions_to_records(predictions_df: pd.DataFrame) -> list[dict[str, Any]]:
    """Convert prediction rows to plain dictionaries."""
    return predictions_df.to_dict(orient="records")


def _optional_iso_date(value: Any) -> str | None:
    if value is None:
        return None
    return pd.Timestamp(value).date().isoformat()
