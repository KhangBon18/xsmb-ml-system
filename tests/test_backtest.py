"""Tests for Phase 5 baselines, metrics, and walk-forward backtest."""

from __future__ import annotations

import math
from datetime import date, timedelta

import pandas as pd
import pytest

from xsmb.config import (
    TARGET_DB_2CANG,
    TARGET_DB_3CANG,
    TARGET_LOTO_2D_ALL_PRIZES,
)
from xsmb.models.backtest import run_walk_forward_backtest
from xsmb.models.baseline import score_baseline_candidates
from xsmb.models.evaluate import (
    avg_hits_at_k,
    brier_score,
    calibration_by_bucket,
    evaluate_predictions,
    hit_rate_at_k,
    log_loss,
    precision_at_k,
    recall_at_k,
)


def _feature_df() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "target_date": "2024-02-01",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "05",
                "label": 1,
                "hit_count": 2,
                "freq_30": 8,
                "freq_90": 12,
                "rolling_hit_rate_30": 0.50,
                "rolling_hit_rate_90": 0.40,
                "current_gap": 3,
            },
            {
                "target_date": "2024-02-01",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "00",
                "label": 0,
                "hit_count": 0,
                "freq_30": 1,
                "freq_90": 2,
                "rolling_hit_rate_30": 0.10,
                "rolling_hit_rate_90": 0.05,
                "current_gap": 1,
            },
            {
                "target_date": "2024-02-01",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "08",
                "label": 0,
                "hit_count": 0,
                "freq_30": 3,
                "freq_90": 30,
                "rolling_hit_rate_30": 0.20,
                "rolling_hit_rate_90": 0.70,
                "current_gap": 9,
            },
            {
                "target_date": "2024-02-02",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "05",
                "label": 0,
                "hit_count": 0,
                "freq_30": 2,
                "freq_90": 4,
                "rolling_hit_rate_30": 0.20,
                "rolling_hit_rate_90": 0.30,
                "current_gap": 5,
            },
            {
                "target_date": "2024-02-02",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "00",
                "label": 1,
                "hit_count": 1,
                "freq_30": 5,
                "freq_90": 6,
                "rolling_hit_rate_30": 0.60,
                "rolling_hit_rate_90": 0.20,
                "current_gap": 2,
            },
        ]
    )


def _metric_predictions() -> pd.DataFrame:
    return pd.DataFrame(
        [
            {
                "target_date": "2024-02-01",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "05",
                "probability": 0.8,
                "rank": 1,
                "label": 1,
                "hit_count": 3,
            },
            {
                "target_date": "2024-02-01",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "00",
                "probability": 0.2,
                "rank": 2,
                "label": 0,
                "hit_count": 0,
            },
            {
                "target_date": "2024-02-01",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "08",
                "probability": 0.1,
                "rank": 3,
                "label": 1,
                "hit_count": 1,
            },
            {
                "target_date": "2024-02-02",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "05",
                "probability": 0.7,
                "rank": 1,
                "label": 0,
                "hit_count": 0,
            },
            {
                "target_date": "2024-02-02",
                "target_type": TARGET_LOTO_2D_ALL_PRIZES,
                "candidate_number": "00",
                "probability": 0.6,
                "rank": 2,
                "label": 1,
                "hit_count": 2,
            },
        ]
    )


def _history_df(
    target_type: str = TARGET_LOTO_2D_ALL_PRIZES,
    candidates: list[str] | None = None,
    num_dates: int = 35,
    hits: dict[str, dict[int, tuple[int, int]]] | None = None,
) -> pd.DataFrame:
    candidates = candidates or ["00", "05", "08"]
    hits = hits or {"05": {1: (1, 1), 5: (1, 2), 20: (1, 1), 32: (1, 1)}}
    start = date(2024, 1, 1)
    rows: list[dict[str, object]] = []
    for day_index in range(num_dates):
        draw_date = (start + timedelta(days=day_index)).isoformat()
        for candidate in candidates:
            label, hit_count = hits.get(candidate, {}).get(day_index, (0, 0))
            rows.append(
                {
                    "draw_date": draw_date,
                    "target_type": target_type,
                    "candidate_number": candidate,
                    "label": label,
                    "hit_count": hit_count,
                }
            )
    return pd.DataFrame(rows)


def test_random_uniform_equal_probabilities_and_lexicographic_ranking() -> None:
    predictions = score_baseline_candidates(_feature_df(), "random_uniform")
    first_date = predictions[predictions["target_date"] == "2024-02-01"]

    assert all(value == pytest.approx(1 / 3) for value in first_date["probability"])
    assert list(first_date["candidate_number"]) == ["00", "05", "08"]
    assert list(first_date["rank"]) == [1, 2, 3]


def test_frequency_30_ranks_higher_rolling_hit_rate() -> None:
    predictions = score_baseline_candidates(_feature_df(), "frequency_30")
    first_date = predictions[predictions["target_date"] == "2024-02-01"]

    assert list(first_date["candidate_number"])[:3] == ["05", "08", "00"]
    assert first_date.iloc[0]["probability"] == pytest.approx(0.50)


def test_frequency_90_ranks_higher_rolling_hit_rate() -> None:
    predictions = score_baseline_candidates(_feature_df(), "frequency_90")
    first_date = predictions[predictions["target_date"] == "2024-02-01"]

    assert list(first_date["candidate_number"])[:3] == ["08", "05", "00"]
    assert first_date.iloc[0]["probability"] == pytest.approx(0.70)


def test_gap_rank_ranks_smaller_current_gap_higher() -> None:
    predictions = score_baseline_candidates(_feature_df(), "gap_rank")
    first_date = predictions[predictions["target_date"] == "2024-02-01"]

    assert list(first_date["candidate_number"])[:3] == ["00", "05", "08"]
    assert first_date.iloc[0]["score"] == pytest.approx(1 / 2)


def test_baseline_preserves_candidate_strings_and_leading_zeros() -> None:
    feature_df = pd.DataFrame(
        [
            {
                "target_date": "2024-02-01",
                "target_type": TARGET_DB_3CANG,
                "candidate_number": candidate,
                "label": 0,
                "hit_count": 0,
            }
            for candidate in ["008", "000"]
        ]
    )

    predictions = score_baseline_candidates(feature_df, "random_uniform")

    assert list(predictions["candidate_number"]) == ["000", "008"]
    assert all(isinstance(value, str) for value in predictions["candidate_number"])


def test_unsupported_baseline_raises_value_error() -> None:
    with pytest.raises(ValueError, match="Unsupported baseline"):
        score_baseline_candidates(_feature_df(), "not_a_model")


def test_missing_required_feature_columns_raise_value_error() -> None:
    with pytest.raises(ValueError, match="missing required columns"):
        score_baseline_candidates(_feature_df().drop(columns=["current_gap"]), "gap_rank")


def test_frequency_fallback_uses_frequency_count_when_rolling_rate_missing() -> None:
    feature_df = _feature_df().drop(columns=["rolling_hit_rate_30"])

    predictions = score_baseline_candidates(feature_df, "frequency_30")
    first = predictions[predictions["target_date"] == "2024-02-01"].iloc[0]

    assert first["candidate_number"] == "05"
    assert first["probability"] == pytest.approx(8 / 30)


def test_brier_score_computes_expected_value() -> None:
    assert brier_score([1, 0], [0.75, 0.25]) == pytest.approx(0.0625)


def test_log_loss_clips_probabilities_and_is_finite() -> None:
    value = log_loss([1, 0], [1.0, 0.0])

    assert math.isfinite(value)
    assert value >= 0.0


def test_precision_hit_rate_avg_hits_and_recall_at_k() -> None:
    predictions = _metric_predictions()

    assert precision_at_k(predictions, 2) == pytest.approx(0.5)
    assert hit_rate_at_k(predictions, 2) == pytest.approx(1.0)
    assert avg_hits_at_k(predictions, 2) == pytest.approx(2.5)
    assert recall_at_k(predictions, 2) == pytest.approx(0.75)


def test_calibration_by_bucket_returns_deterministic_bucket_stats() -> None:
    calibration = calibration_by_bucket(_metric_predictions(), n_buckets=2)

    assert list(calibration.columns) == [
        "bucket",
        "count",
        "avg_probability",
        "empirical_hit_rate",
    ]
    assert list(calibration["bucket"]) == [0, 1]
    assert list(calibration["count"]) == [2, 3]


def test_evaluate_predictions_returns_expected_summary_keys() -> None:
    summary = evaluate_predictions(_metric_predictions(), top_k_values=(1, 2))

    assert {
        "brier_score",
        "log_loss",
        "row_count",
        "date_count",
        "precision_at_1",
        "hit_rate_at_1",
        "avg_hits_at_1",
        "recall_at_1",
        "precision_at_2",
        "hit_rate_at_2",
        "avg_hits_at_2",
        "recall_at_2",
    }.issubset(summary)
    assert summary["row_count"] == 5
    assert summary["date_count"] == 2


@pytest.mark.parametrize(
    ("target_type", "candidates"),
    [
        (TARGET_LOTO_2D_ALL_PRIZES, ["00", "05", "08"]),
        (TARGET_DB_2CANG, ["00", "05", "08"]),
        (TARGET_DB_3CANG, ["000", "005", "008"]),
    ],
)
def test_run_walk_forward_backtest_works_for_all_target_types(
    target_type: str, candidates: list[str]
) -> None:
    result = run_walk_forward_backtest(
        _history_df(target_type=target_type, candidates=candidates),
        target_type=target_type,
        model_name="frequency_30",
        min_history_days=30,
        top_k_values=(1, 2),
    )

    assert result["target_type"] == target_type
    assert result["model_name"] == "frequency_30"
    assert not result["predictions"].empty
    assert result["summary"]["date_count"] == 5
    assert list(result["calibration"].columns) == [
        "bucket",
        "count",
        "avg_probability",
        "empirical_hit_rate",
    ]


def test_backtest_explicit_no_leakage_for_target_date_hit() -> None:
    history = _history_df(
        candidates=["00", "08"],
        num_dates=35,
        hits={"08": {30: (1, 1)}},
    )

    result = run_walk_forward_backtest(
        history,
        target_type=TARGET_LOTO_2D_ALL_PRIZES,
        model_name="frequency_30",
        start_date="2024-01-31",
        end_date="2024-01-31",
        min_history_days=30,
        top_k_values=(1,),
    )
    row = result["predictions"][
        result["predictions"]["candidate_number"] == "08"
    ].iloc[0]

    assert row["label"] == 1
    assert row["score"] == 0.0
    assert row["probability"] == 0.0


def test_backtest_min_history_days_suppresses_early_dates() -> None:
    result = run_walk_forward_backtest(
        _history_df(num_dates=35),
        target_type=TARGET_LOTO_2D_ALL_PRIZES,
        model_name="random_uniform",
        min_history_days=30,
        top_k_values=(1,),
    )

    assert result["predictions"]["target_date"].min() == "2024-01-31"
    assert result["summary"]["date_count"] == 5


def test_backtest_start_date_and_end_date_limit_evaluated_dates() -> None:
    result = run_walk_forward_backtest(
        _history_df(num_dates=40),
        target_type=TARGET_LOTO_2D_ALL_PRIZES,
        model_name="random_uniform",
        start_date="2024-02-02",
        end_date="2024-02-04",
        min_history_days=30,
        top_k_values=(1,),
    )

    assert sorted(result["predictions"]["target_date"].unique()) == [
        "2024-02-02",
        "2024-02-03",
        "2024-02-04",
    ]


def test_backtest_prediction_columns_and_rank_start() -> None:
    result = run_walk_forward_backtest(
        _history_df(num_dates=32),
        target_type=TARGET_LOTO_2D_ALL_PRIZES,
        model_name="gap_rank",
        min_history_days=30,
        top_k_values=(1,),
    )
    predictions = result["predictions"]

    assert {
        "target_date",
        "target_type",
        "candidate_number",
        "score",
        "probability",
        "rank",
        "label",
        "hit_count",
        "model_name",
    }.issubset(predictions.columns)
    assert predictions.groupby("target_date")["rank"].min().eq(1).all()
    assert "05" in set(predictions["candidate_number"])
    assert all(isinstance(value, str) for value in predictions["candidate_number"])
