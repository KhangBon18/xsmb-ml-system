"""Prediction utilities for trained ML probability-ranking models."""

from __future__ import annotations

from typing import Any, Optional

import numpy as np
import pandas as pd

PREDICT_REQUIRED_COLUMNS: set[str] = {
    "target_date",
    "target_type",
    "candidate_number",
}


def predict_probabilities(
    trained_model: dict[str, Any],
    feature_df: pd.DataFrame,
    target_date: Optional[str] = None,
    top_k: Optional[int] = None,
) -> pd.DataFrame:
    """Generate ranked probability predictions for candidate feature rows."""
    _validate_trained_model(trained_model)
    _validate_feature_frame(feature_df)
    if top_k is not None and top_k <= 0:
        raise ValueError("top_k must be positive")

    target_type = trained_model["target_type"]
    feature_columns = list(trained_model["feature_columns"])
    missing_features = sorted(set(feature_columns) - set(feature_df.columns))
    if missing_features:
        raise ValueError(f"feature_df is missing feature columns: {missing_features}")

    df = feature_df[feature_df["target_type"] == target_type].copy()
    if target_date is not None:
        target_date_str = pd.Timestamp(target_date).date().isoformat()
        df = df[pd.to_datetime(df["target_date"]).dt.date.astype(str) == target_date_str]
    if df.empty:
        return _empty_predictions(include_labels={"label", "hit_count"}.issubset(feature_df.columns))

    df["candidate_number"] = df["candidate_number"].astype(str)
    probabilities = _predict_probability_values(trained_model["model"], df[feature_columns])
    df["probability"] = np.clip(probabilities, 0.0, 1.0)
    if df["probability"].isna().any():
        raise ValueError("Model produced NaN probabilities")
    df["model_name"] = trained_model["model_name"]

    ranked = df.sort_values(
        ["target_date", "probability", "candidate_number"],
        ascending=[True, False, True],
        kind="mergesort",
    ).reset_index(drop=True)
    ranked["rank"] = ranked.groupby("target_date").cumcount() + 1
    if top_k is not None:
        ranked = ranked[ranked["rank"] <= top_k].copy()

    output_columns = [
        "target_date",
        "target_type",
        "candidate_number",
        "probability",
        "rank",
        "model_name",
    ]
    if "label" in ranked.columns:
        output_columns.append("label")
    if "hit_count" in ranked.columns:
        output_columns.append("hit_count")
    return ranked[output_columns].sort_values(
        ["target_date", "rank"], kind="mergesort", ignore_index=True
    )


def _predict_probability_values(model: Any, features: pd.DataFrame) -> np.ndarray:
    if hasattr(model, "predict_proba"):
        probabilities = model.predict_proba(features)
        if probabilities.ndim == 2:
            if probabilities.shape[1] == 1:
                classes = getattr(model, "classes_", np.array([1]))
                return np.ones(len(features)) if classes[0] == 1 else np.zeros(len(features))
            return probabilities[:, 1]
        return probabilities

    if hasattr(model, "decision_function"):
        scores = model.decision_function(features)
        return 1.0 / (1.0 + np.exp(-scores))

    raise ValueError("Trained model must expose predict_proba or decision_function")


def _validate_trained_model(trained_model: dict[str, Any]) -> None:
    required_keys = {"model_name", "target_type", "model", "feature_columns"}
    missing_keys = sorted(required_keys - set(trained_model))
    if missing_keys:
        raise ValueError(f"trained_model is missing required keys: {missing_keys}")


def _validate_feature_frame(feature_df: pd.DataFrame) -> None:
    missing_columns = sorted(PREDICT_REQUIRED_COLUMNS - set(feature_df.columns))
    if missing_columns:
        raise ValueError(f"feature_df is missing required columns: {missing_columns}")


def _empty_predictions(include_labels: bool) -> pd.DataFrame:
    columns = [
        "target_date",
        "target_type",
        "candidate_number",
        "probability",
        "rank",
        "model_name",
    ]
    if include_labels:
        columns.extend(["label", "hit_count"])
    return pd.DataFrame(columns=columns)
