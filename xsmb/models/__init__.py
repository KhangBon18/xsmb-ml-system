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
from xsmb.models.predict import predict_probabilities
from xsmb.models.train import (
    SUPPORTED_ML_MODELS,
    load_model_artifact,
    save_model_artifact,
    train_model,
)

__all__ = [
    "SUPPORTED_BASELINES",
    "SUPPORTED_ML_MODELS",
    "avg_hits_at_k",
    "brier_score",
    "calibration_by_bucket",
    "evaluate_predictions",
    "hit_rate_at_k",
    "log_loss",
    "precision_at_k",
    "predictions_to_records",
    "predict_probabilities",
    "recall_at_k",
    "run_walk_forward_backtest",
    "save_model_artifact",
    "score_baseline_candidates",
    "summarize_backtest_result",
    "load_model_artifact",
    "train_model",
]
