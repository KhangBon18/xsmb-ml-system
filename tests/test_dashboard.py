"""Tests for the local Streamlit dashboard helpers."""

from __future__ import annotations

import pathlib
import socket

import pandas as pd
import pytest


def _prediction_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "target_date": "2024-01-02",
                "target_type": "loto_2d_all_prizes",
                "candidate_number": "05",
                "probability": 0.42,
                "rank": 2,
                "model_name": "frequency_30",
            },
            {
                "target_date": "2024-01-01",
                "target_type": "loto_2d_all_prizes",
                "candidate_number": "00",
                "probability": 0.72,
                "rank": 1,
                "model_name": "frequency_30",
            },
            {
                "target_date": "2024-01-01",
                "target_type": "db_3cang",
                "candidate_number": "008",
                "probability": 0.12,
                "rank": 1,
                "model_name": "frequency_30",
            },
            {
                "target_date": "2024-01-02",
                "target_type": "loto_2d_all_prizes",
                "candidate_number": "10",
                "probability": 0.21,
                "rank": 3,
                "model_name": "frequency_30",
            },
        ]
    )


def test_dashboard_module_imports_without_launching_streamlit() -> None:
    import xsmb.dashboard.streamlit_app as dashboard

    assert callable(dashboard.prepare_predictions_table)


def test_prepare_predictions_table_returns_expected_columns() -> None:
    from xsmb.dashboard.streamlit_app import prepare_predictions_table

    table = prepare_predictions_table(_prediction_df(), top_k=20)

    assert list(table.columns) == [
        "target_date",
        "target_type",
        "candidate_number",
        "probability",
        "rank",
        "model_name",
    ]


def test_prepare_predictions_table_preserves_leading_zero_candidate_strings() -> None:
    from xsmb.dashboard.streamlit_app import prepare_predictions_table

    table = prepare_predictions_table(_prediction_df(), top_k=20)

    assert set(table["candidate_number"]) >= {"00", "05", "008"}
    assert all(isinstance(value, str) for value in table["candidate_number"])


def test_prepare_predictions_table_applies_top_k_by_rank() -> None:
    from xsmb.dashboard.streamlit_app import prepare_predictions_table

    table = prepare_predictions_table(_prediction_df(), top_k=2)

    assert set(table["candidate_number"]) == {"00", "05", "008"}
    assert table["rank"].max() <= 2


def test_prepare_predictions_table_filters_target_type() -> None:
    from xsmb.dashboard.streamlit_app import prepare_predictions_table

    table = prepare_predictions_table(_prediction_df(), target_type="db_3cang", top_k=20)

    assert list(table["target_type"]) == ["db_3cang"]
    assert list(table["candidate_number"]) == ["008"]


def test_prepare_predictions_table_does_not_mutate_input_dataframe() -> None:
    from xsmb.dashboard.streamlit_app import prepare_predictions_table

    predictions = _prediction_df()
    original = predictions.copy(deep=True)

    prepare_predictions_table(predictions, target_type="loto_2d_all_prizes", top_k=2)

    pd.testing.assert_frame_equal(predictions, original)


def test_missing_required_prediction_columns_raises_value_error() -> None:
    from xsmb.dashboard.streamlit_app import validate_prediction_columns

    with pytest.raises(ValueError, match="missing required columns"):
        validate_prediction_columns(pd.DataFrame({"candidate_number": ["00"]}))


def test_invalid_top_k_raises_value_error() -> None:
    from xsmb.dashboard.streamlit_app import prepare_predictions_table

    with pytest.raises(ValueError, match="top_k must be a positive integer"):
        prepare_predictions_table(_prediction_df(), top_k=0)


def test_prepare_probability_distribution_returns_deterministic_bucket_counts() -> None:
    from xsmb.dashboard.streamlit_app import prepare_probability_distribution

    distribution = prepare_probability_distribution(_prediction_df())

    assert list(distribution.columns) == [
        "probability_bucket",
        "bucket_start",
        "bucket_end",
        "count",
    ]
    assert len(distribution) == 10
    assert distribution["count"].sum() == 4
    assert list(distribution["count"]) == [0, 1, 1, 0, 1, 0, 0, 1, 0, 0]


def test_prepare_calibration_table_preserves_expected_columns() -> None:
    from xsmb.dashboard.streamlit_app import prepare_calibration_table

    calibration = pd.DataFrame(
        {
            "bucket": [0, 1],
            "count": [3, 5],
            "avg_probability": [0.05, 0.15],
            "empirical_hit_rate": [0.0, 0.2],
            "extra": ["ignore", "ignore"],
        }
    )

    table = prepare_calibration_table(calibration)

    assert list(table.columns) == [
        "bucket",
        "count",
        "avg_probability",
        "empirical_hit_rate",
    ]


def test_prepare_topk_summary_from_summary_dict() -> None:
    from xsmb.dashboard.streamlit_app import prepare_topk_summary

    table = prepare_topk_summary(
        {
            "brier_score": 0.12,
            "precision_at_5": 0.2,
            "hit_rate_at_5": 0.7,
            "avg_hits_at_5": 1.1,
            "recall_at_5": 0.4,
            "precision_at_10": 0.18,
            "hit_rate_at_10": 0.8,
            "avg_hits_at_10": 1.4,
            "recall_at_10": 0.5,
        }
    )

    assert list(table.columns) == ["top_k", "precision", "hit_rate", "avg_hits", "recall"]
    assert list(table["top_k"]) == [5, 10]


def test_dashboard_helpers_do_not_create_real_database() -> None:
    from xsmb.dashboard.streamlit_app import (
        prepare_calibration_table,
        prepare_predictions_table,
        prepare_probability_distribution,
        prepare_topk_summary,
    )

    db_path = pathlib.Path("data/xsmb.sqlite3")
    existed_before = db_path.exists()

    predictions = _prediction_df()
    prepare_predictions_table(predictions)
    prepare_probability_distribution(predictions)
    prepare_topk_summary({"precision_at_5": 0.1})
    prepare_calibration_table(
        pd.DataFrame(
            {
                "bucket": [0],
                "count": [1],
                "avg_probability": [0.05],
                "empirical_hit_rate": [0.0],
            }
        )
    )

    if not existed_before:
        assert not db_path.exists(), "Dashboard helpers must not create the real database"


def test_dashboard_helpers_do_not_use_network(monkeypatch: pytest.MonkeyPatch) -> None:
    from xsmb.dashboard.streamlit_app import prepare_predictions_table

    def fail_socket(*_args: object, **_kwargs: object) -> None:
        raise AssertionError("Dashboard helpers must not open network sockets")

    monkeypatch.setattr(socket, "socket", fail_socket)

    table = prepare_predictions_table(_prediction_df(), top_k=1)

    assert set(table["candidate_number"]) == {"00", "008"}
