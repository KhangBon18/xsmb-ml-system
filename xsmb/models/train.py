"""ML training utilities for probability-ranking models."""

from __future__ import annotations

import pickle
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Optional

import pandas as pd
from sklearn.calibration import CalibratedClassifierCV
from sklearn.ensemble import RandomForestClassifier
from sklearn.impute import SimpleImputer
from sklearn.linear_model import LogisticRegression
from sklearn.pipeline import Pipeline
from sklearn.preprocessing import StandardScaler

try:  # pragma: no cover - availability depends on sklearn version.
    from sklearn.ensemble import HistGradientBoostingClassifier
except ImportError:  # pragma: no cover
    HistGradientBoostingClassifier = None  # type: ignore[assignment]

from xsmb.processing.transform import candidate_space

SUPPORTED_ML_MODELS: set[str] = {
    "logistic_regression",
    "random_forest",
    "hist_gradient_boosting",
}

NON_FEATURE_COLUMNS: set[str] = {
    "target_date",
    "draw_date",
    "target_type",
    "candidate_number",
    "label",
    "hit_count",
    "rank",
    "score",
    "probability",
    "model_name",
}


def train_model(
    feature_df: pd.DataFrame,
    target_type: str,
    model_name: str,
    feature_columns: Optional[list[str]] = None,
    model_params: Optional[dict[str, Any]] = None,
    random_state: int = 42,
    calibrate: bool = True,
) -> dict[str, Any]:
    """Train a deterministic sklearn classifier for one explicit target type."""
    candidate_space(target_type)
    _validate_model_name(model_name)
    _validate_training_frame(feature_df)

    df = feature_df[feature_df["target_type"] == target_type].copy()
    if df.empty:
        raise ValueError(f"No training rows found for target_type {target_type!r}")
    df["candidate_number"] = df["candidate_number"].astype(str)

    selected_features = _select_feature_columns(df, feature_columns)
    y = df["label"].astype(int)
    class_counts = y.value_counts()
    if len(class_counts) < 2:
        raise ValueError("Training data must contain both positive and negative labels")

    estimator = _build_estimator(model_name, model_params or {}, random_state)
    fitted_model = estimator
    calibrated = False

    if calibrate and model_name in {"random_forest", "hist_gradient_boosting"}:
        cv = _calibration_cv(y)
        if cv is not None:
            fitted_model = CalibratedClassifierCV(estimator=estimator, cv=cv)
            calibrated = True

    fitted_model.fit(df[selected_features], y)

    params = dict(model_params or {})
    params.setdefault("random_state", random_state)
    return {
        "model_name": model_name,
        "target_type": target_type,
        "model": fitted_model,
        "pipeline": fitted_model,
        "feature_columns": selected_features,
        "trained_at": datetime.now(timezone.utc).isoformat(),
        "row_count": int(len(df)),
        "positive_count": int(y.sum()),
        "params": params,
        "calibrated": calibrated,
        "training_summary": {
            "negative_count": int((y == 0).sum()),
            "positive_rate": float(y.mean()),
            "candidate_count": int(df["candidate_number"].nunique()),
        },
    }


def save_model_artifact(
    trained_model: dict[str, Any], artifact_dir: str | Path = "data/models"
) -> str:
    """Persist a trained model dictionary to a pickle artifact."""
    _validate_trained_model(trained_model)
    artifact_path = Path(artifact_dir)
    artifact_path.mkdir(parents=True, exist_ok=True)
    timestamp = datetime.now(timezone.utc).strftime("%Y%m%d%H%M%S%f")
    filename = (
        f"{trained_model['target_type']}_{trained_model['model_name']}_{timestamp}.pkl"
    )
    output_path = artifact_path / filename
    with output_path.open("wb") as file_obj:
        pickle.dump(trained_model, file_obj)
    return str(output_path)


def load_model_artifact(path: str | Path) -> dict[str, Any]:
    """Load a trained model dictionary from a pickle artifact."""
    with Path(path).open("rb") as file_obj:
        trained_model = pickle.load(file_obj)
    _validate_trained_model(trained_model)
    return trained_model


def _validate_model_name(model_name: str) -> None:
    if model_name not in SUPPORTED_ML_MODELS:
        raise ValueError(f"Unsupported ML model_name: {model_name!r}")
    if model_name == "hist_gradient_boosting" and HistGradientBoostingClassifier is None:
        raise ValueError("hist_gradient_boosting is not available in this sklearn version")


def _validate_training_frame(feature_df: pd.DataFrame) -> None:
    if feature_df.empty:
        raise ValueError("feature_df must not be empty")
    if "label" not in feature_df.columns:
        raise ValueError("feature_df is missing required column: label")
    for column in ("target_type", "candidate_number"):
        if column not in feature_df.columns:
            raise ValueError(f"feature_df is missing required column: {column}")


def _select_feature_columns(
    df: pd.DataFrame, feature_columns: Optional[list[str]]
) -> list[str]:
    if feature_columns is not None:
        missing_columns = sorted(set(feature_columns) - set(df.columns))
        if missing_columns:
            raise ValueError(f"feature_df is missing feature columns: {missing_columns}")
        selected = list(feature_columns)
    else:
        selected = [
            column
            for column in df.columns
            if column not in NON_FEATURE_COLUMNS and pd.api.types.is_numeric_dtype(df[column])
        ]

    if not selected:
        raise ValueError("No usable numeric feature columns found")
    non_numeric = [
        column
        for column in selected
        if not pd.api.types.is_numeric_dtype(df[column])
    ]
    if non_numeric:
        raise ValueError(f"Feature columns must be numeric: {non_numeric}")
    return selected


def _build_estimator(
    model_name: str, model_params: dict[str, Any], random_state: int
) -> Pipeline:
    if model_name == "logistic_regression":
        params = {
            "max_iter": 1000,
            "class_weight": "balanced",
            "random_state": random_state,
            **model_params,
        }
        classifier = LogisticRegression(**params)
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("scaler", StandardScaler()),
                ("classifier", classifier),
            ]
        )

    if model_name == "random_forest":
        params = {
            "n_estimators": 100,
            "max_depth": 6,
            "min_samples_leaf": 2,
            "class_weight": "balanced",
            "random_state": random_state,
            "n_jobs": 1,
            **model_params,
        }
        classifier = RandomForestClassifier(**params)
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("classifier", classifier),
            ]
        )

    if model_name == "hist_gradient_boosting":
        if HistGradientBoostingClassifier is None:
            raise ValueError("hist_gradient_boosting is not available in this sklearn version")
        params = {
            "max_iter": 100,
            "max_leaf_nodes": 15,
            "learning_rate": 0.05,
            "random_state": random_state,
            **model_params,
        }
        classifier = HistGradientBoostingClassifier(**params)
        return Pipeline(
            [
                ("imputer", SimpleImputer(strategy="median")),
                ("classifier", classifier),
            ]
        )

    raise ValueError(f"Unsupported ML model_name: {model_name!r}")


def _calibration_cv(y: pd.Series) -> int | None:
    min_class_count = int(y.value_counts().min())
    if min_class_count < 3:
        return None
    return min(3, min_class_count)


def _validate_trained_model(trained_model: dict[str, Any]) -> None:
    required_keys = {
        "model_name",
        "target_type",
        "model",
        "feature_columns",
    }
    missing_keys = sorted(required_keys - set(trained_model))
    if missing_keys:
        raise ValueError(f"trained_model is missing required keys: {missing_keys}")
