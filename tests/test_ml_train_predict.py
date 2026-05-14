"""Tests for Phase 6 ML training, prediction, and artifacts."""

from __future__ import annotations

from datetime import date, timedelta
from pathlib import Path

import numpy as np
import pandas as pd
import pytest

import xsmb.models.train as train_module
from xsmb.config import (
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
    TARGET_LOTO_2D_ALL_PRIZES,
)
from xsmb.models.evaluate import evaluate_predictions
from xsmb.models.predict import predict_probabilities
from xsmb.models.train import (
    load_model_artifact,
    save_model_artifact,
    train_model,
)

FEATURE_COLUMNS = [
    "freq_7",
    "freq_30",
    "freq_90",
    "hit_count_sum_30",
    "current_gap",
    "rolling_hit_rate_30",
    "rolling_hit_rate_90",
]


def _feature_df(
    target_type: str = TARGET_LOTO_2D_ALL_PRIZES,
    candidates: list[str] | None = None,
    num_dates: int = 45,
) -> pd.DataFrame:
    candidates = candidates or ["00", "05", "08"]
    start = date(2024, 1, 1)
    rows: list[dict[str, object]] = []
    for day_index in range(num_dates):
        target_date = (start + timedelta(days=day_index)).isoformat()
        for candidate_index, candidate in enumerate(candidates):
            signal = (day_index + candidate_index) % len(candidates)
            label = 1 if signal == 0 else 0
            hit_count = 2 if label and target_type == TARGET_LOTO_2D_ALL_PRIZES else int(label)
            freq_7 = (day_index % 7) + (2 if candidate.endswith("5") else 0)
            freq_30 = (day_index % 10) + (5 if candidate.endswith("5") else 1 if candidate.endswith("8") else 0)
            freq_90 = freq_30 + candidate_index
            rows.append(
                {
                    "target_date": target_date,
                    "target_type": target_type,
                    "candidate_number": candidate,
                    "label": label,
                    "hit_count": hit_count,
                    "freq_7": freq_7,
                    "freq_30": freq_30,
                    "freq_90": freq_90,
                    "hit_count_sum_30": freq_30 + hit_count,
                    "current_gap": (candidate_index + day_index) % 9,
                    "rolling_hit_rate_30": min(freq_30 / 30.0, 1.0),
                    "rolling_hit_rate_90": min(freq_90 / 90.0, 1.0),
                }
            )
    return pd.DataFrame(rows)


def test_train_model_works_for_logistic_regression() -> None:
    trained = train_model(
        _feature_df(),
        TARGET_LOTO_2D_ALL_PRIZES,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )

    assert trained["model_name"] == "logistic_regression"
    assert trained["target_type"] == TARGET_LOTO_2D_ALL_PRIZES
    assert trained["feature_columns"] == FEATURE_COLUMNS
    assert trained["row_count"] > 0
    assert trained["positive_count"] > 0


def test_train_model_works_for_random_forest() -> None:
    trained = train_model(
        _feature_df(),
        TARGET_LOTO_2D_ALL_PRIZES,
        "random_forest",
        feature_columns=FEATURE_COLUMNS,
        model_params={"n_estimators": 10, "max_depth": 3},
        random_state=7,
    )

    assert trained["model_name"] == "random_forest"
    assert isinstance(trained["calibrated"], bool)


def test_train_model_hist_gradient_boosting_available_or_graceful() -> None:
    if train_module.HistGradientBoostingClassifier is None:
        with pytest.raises(ValueError, match="not available"):
            train_model(
                _feature_df(),
                TARGET_LOTO_2D_ALL_PRIZES,
                "hist_gradient_boosting",
                feature_columns=FEATURE_COLUMNS,
            )
        return

    trained = train_model(
        _feature_df(),
        TARGET_LOTO_2D_ALL_PRIZES,
        "hist_gradient_boosting",
        feature_columns=FEATURE_COLUMNS,
        model_params={"max_iter": 20},
        random_state=7,
    )
    assert trained["model_name"] == "hist_gradient_boosting"


def test_train_model_rejects_unsupported_model_name() -> None:
    with pytest.raises(ValueError, match="Unsupported ML model_name"):
        train_model(_feature_df(), TARGET_LOTO_2D_ALL_PRIZES, "not_a_model")


def test_train_model_rejects_empty_data() -> None:
    with pytest.raises(ValueError, match="must not be empty"):
        train_model(pd.DataFrame(), TARGET_LOTO_2D_ALL_PRIZES, "logistic_regression")


def test_train_model_rejects_one_class_training_data() -> None:
    feature_df = _feature_df()
    feature_df["label"] = 0

    with pytest.raises(ValueError, match="both positive and negative"):
        train_model(feature_df, TARGET_LOTO_2D_ALL_PRIZES, "logistic_regression")


def test_train_model_rejects_missing_label() -> None:
    with pytest.raises(ValueError, match="label"):
        train_model(
            _feature_df().drop(columns=["label"]),
            TARGET_LOTO_2D_ALL_PRIZES,
            "logistic_regression",
        )


def test_train_model_rejects_no_usable_numeric_features() -> None:
    metadata_only = _feature_df()[[
        "target_date",
        "target_type",
        "candidate_number",
        "label",
        "hit_count",
    ]]

    with pytest.raises(ValueError, match="No usable numeric feature"):
        train_model(metadata_only, TARGET_LOTO_2D_ALL_PRIZES, "logistic_regression")


def test_train_model_preserves_candidate_number_strings_in_prediction_flow() -> None:
    feature_df = _feature_df(target_type=TARGET_DB_3CANG, candidates=["000", "005", "008"])
    trained = train_model(
        feature_df,
        TARGET_DB_3CANG,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )
    predictions = predict_probabilities(trained, feature_df, target_date="2024-02-01")

    assert {"000", "005", "008"} == set(predictions["candidate_number"])
    assert all(isinstance(value, str) for value in predictions["candidate_number"])


def test_predict_probabilities_returns_required_columns_and_valid_probabilities() -> None:
    feature_df = _feature_df()
    trained = train_model(
        feature_df,
        TARGET_LOTO_2D_ALL_PRIZES,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )

    predictions = predict_probabilities(trained, feature_df, target_date="2024-02-01")

    assert {
        "target_date",
        "target_type",
        "candidate_number",
        "probability",
        "rank",
        "model_name",
        "label",
        "hit_count",
    }.issubset(predictions.columns)
    assert predictions["probability"].between(0.0, 1.0).all()
    assert not predictions["probability"].isna().any()


def test_predict_rank_starts_at_one_for_each_target_date() -> None:
    feature_df = _feature_df()
    trained = train_model(
        feature_df,
        TARGET_LOTO_2D_ALL_PRIZES,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )

    predictions = predict_probabilities(trained, feature_df)

    assert predictions.groupby("target_date")["rank"].min().eq(1).all()


class EqualProbabilityModel:
    """Test model that returns equal positive probabilities."""

    def predict_proba(self, features):
        return np.column_stack([np.full(len(features), 0.5), np.full(len(features), 0.5)])


def test_predict_sorting_uses_probability_then_candidate_lexicographic() -> None:
    feature_df = _feature_df(target_type=TARGET_DB_3CANG, candidates=["008", "000", "005"], num_dates=1)
    trained = {
        "model_name": "equal_model",
        "target_type": TARGET_DB_3CANG,
        "model": EqualProbabilityModel(),
        "feature_columns": FEATURE_COLUMNS,
    }

    predictions = predict_probabilities(trained, feature_df)

    assert list(predictions["candidate_number"]) == ["000", "005", "008"]
    assert list(predictions["rank"]) == [1, 2, 3]


def test_predict_top_k_filters_per_target_date() -> None:
    feature_df = _feature_df(num_dates=3)
    trained = {
        "model_name": "equal_model",
        "target_type": TARGET_LOTO_2D_ALL_PRIZES,
        "model": EqualProbabilityModel(),
        "feature_columns": FEATURE_COLUMNS,
    }

    predictions = predict_probabilities(trained, feature_df, top_k=2)

    assert predictions.groupby("target_date").size().eq(2).all()
    assert predictions.groupby("target_date")["rank"].max().eq(2).all()


def test_predict_target_date_filter_works() -> None:
    feature_df = _feature_df(num_dates=5)
    trained = {
        "model_name": "equal_model",
        "target_type": TARGET_LOTO_2D_ALL_PRIZES,
        "model": EqualProbabilityModel(),
        "feature_columns": FEATURE_COLUMNS,
    }

    predictions = predict_probabilities(trained, feature_df, target_date="2024-01-03")

    assert set(predictions["target_date"]) == {"2024-01-03"}


def test_save_and_load_model_artifact_roundtrip(tmp_path: Path) -> None:
    feature_df = _feature_df()
    trained = train_model(
        feature_df,
        TARGET_LOTO_2D_ALL_PRIZES,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )

    artifact_path = save_model_artifact(trained, artifact_dir=tmp_path)
    loaded = load_model_artifact(artifact_path)
    predictions = predict_probabilities(loaded, feature_df, target_date="2024-02-01")

    assert Path(artifact_path).exists()
    assert set(predictions["candidate_number"]) == {"00", "05", "08"}
    assert predictions["probability"].between(0.0, 1.0).all()


def test_loaded_model_predictions_have_same_candidates_and_valid_probabilities(
    tmp_path: Path,
) -> None:
    feature_df = _feature_df()
    trained = train_model(
        feature_df,
        TARGET_LOTO_2D_ALL_PRIZES,
        "random_forest",
        feature_columns=FEATURE_COLUMNS,
        model_params={"n_estimators": 10, "max_depth": 3},
        random_state=42,
        calibrate=False,
    )
    before = predict_probabilities(trained, feature_df, target_date="2024-02-01")
    loaded = load_model_artifact(save_model_artifact(trained, artifact_dir=tmp_path))
    after = predict_probabilities(loaded, feature_df, target_date="2024-02-01")

    assert list(after["candidate_number"]) == list(before["candidate_number"])
    assert after["probability"].between(0.0, 1.0).all()


@pytest.mark.parametrize(
    ("target_type", "candidates"),
    [
        (TARGET_LOTO_2D_ALL_PRIZES, ["00", "05", "08"]),
        (TARGET_DB_2CANG, ["00", "05", "08"]),
        (TARGET_DB_3CANG, ["000", "005", "008"]),
    ],
)
def test_train_predict_integration_works_for_all_target_types(
    target_type: str,
    candidates: list[str],
) -> None:
    feature_df = _feature_df(target_type=target_type, candidates=candidates)
    trained = train_model(
        feature_df,
        target_type,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )
    predictions = predict_probabilities(trained, feature_df, target_date="2024-02-01")

    assert set(predictions["candidate_number"]) == set(candidates)
    assert predictions["probability"].between(0.0, 1.0).all()


def test_predictions_can_be_evaluated_when_labels_are_present() -> None:
    feature_df = _feature_df()
    trained = train_model(
        feature_df,
        TARGET_LOTO_2D_ALL_PRIZES,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )
    predictions = predict_probabilities(trained, feature_df, target_date="2024-02-01")

    summary = evaluate_predictions(predictions, top_k_values=(1, 2))

    assert summary["row_count"] == 3
    assert summary["date_count"] == 1


def test_training_and_prediction_do_not_create_real_database(tmp_path: Path, monkeypatch) -> None:
    monkeypatch.chdir(tmp_path)
    feature_df = _feature_df()
    trained = train_model(
        feature_df,
        TARGET_LOTO_2D_ALL_PRIZES,
        "logistic_regression",
        feature_columns=FEATURE_COLUMNS,
        calibrate=False,
    )
    predict_probabilities(trained, feature_df, target_date="2024-02-01")

    assert not Path("data/xsmb.sqlite3").exists()
