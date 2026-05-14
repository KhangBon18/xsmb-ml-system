"""Model, baseline, metric, and backtest helpers."""

from xsmb.models.backtest import (
    predictions_to_records,
    run_walk_forward_backtest,
    summarize_backtest_result,
)
from xsmb.models.baseline import SUPPORTED_BASELINES, score_baseline_candidates
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

__all__ = [
    "SUPPORTED_BASELINES",
    "avg_hits_at_k",
    "brier_score",
    "calibration_by_bucket",
    "evaluate_predictions",
    "hit_rate_at_k",
    "log_loss",
    "precision_at_k",
    "predictions_to_records",
    "recall_at_k",
    "run_walk_forward_backtest",
    "score_baseline_candidates",
    "summarize_backtest_result",
]
