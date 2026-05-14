"""FastAPI routes for XSMB ML system."""

from __future__ import annotations

import pandas as pd
from typing import Any
from xsmb.config import TARGET_TYPES
from xsmb.models.baseline import SUPPORTED_BASELINES

try:
    from fastapi import APIRouter, HTTPException
    from xsmb.api.schemas import (
        BacktestRequest,
        BacktestResponse,
        HealthResponse,
        TargetsResponse,
        PredictRequest,
        PredictResponse,
    )
    from xsmb.models.backtest import run_walk_forward_backtest
    
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "xsmb-ml-system"}

    @router.get("/targets", response_model=TargetsResponse)
    def get_targets() -> dict[str, list[str]]:
        return {"targets": list(TARGET_TYPES)}

    @router.post("/backtest", response_model=BacktestResponse)
    def run_backtest(request: BacktestRequest) -> dict[str, Any]:
        if request.target_type not in TARGET_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported target_type: {request.target_type}")
        if request.model_name not in SUPPORTED_BASELINES:
            raise HTTPException(status_code=400, detail=f"Unsupported baseline model_name: {request.model_name}")
        if not request.history:
            raise HTTPException(status_code=400, detail="history must not be empty")
        if request.min_history_days < 1:
            raise HTTPException(status_code=400, detail="min_history_days must be >= 1")
        if any(k <= 0 for k in request.top_k_values):
            raise HTTPException(status_code=400, detail="All top_k_values must be positive integers")

        # Convert to DataFrame
        history_df = pd.DataFrame([row.model_dump() if hasattr(row, "model_dump") else row.dict() for row in request.history])
        
        # Ensure candidate_number is string
        history_df["candidate_number"] = history_df["candidate_number"].astype(str)
        # Ensure correct leading zero length if missing, though it should be passed correctly by the user.
        # It's better not to mutate it, just keep it string.

        try:
            result = run_walk_forward_backtest(
                history_df=history_df,
                target_type=request.target_type,
                model_name=request.model_name,
                start_date=request.start_date,
                end_date=request.end_date,
                min_history_days=request.min_history_days,
                top_k_values=tuple(request.top_k_values),
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        return {
            "target_type": result["target_type"],
            "model_name": result["model_name"],
            "summary": result["summary"],
            "prediction_count": len(result["predictions"]),
        }

    @router.post("/predict", response_model=PredictResponse)
    def run_predict(request: PredictRequest) -> dict[str, Any]:
        import pathlib

        if request.target_type not in TARGET_TYPES:
            raise HTTPException(status_code=400, detail=f"Unsupported target_type: {request.target_type}")
        if request.top_k <= 0:
            raise HTTPException(status_code=400, detail="top_k must be > 0")
        if not request.features:
            raise HTTPException(status_code=400, detail="features must not be empty")

        artifact_path = pathlib.Path(request.artifact_path)
        if not artifact_path.exists():
            raise HTTPException(status_code=400, detail=f"artifact_path not found: {request.artifact_path}")

        from xsmb.models.train import load_model_artifact
        from xsmb.models.predict import predict_probabilities

        try:
            trained_model = load_model_artifact(artifact_path)
        except Exception as e:
            raise HTTPException(status_code=400, detail=f"Failed to load artifact: {e}")

        if trained_model["target_type"] != request.target_type:
            raise HTTPException(status_code=400, detail="Artifact target_type does not match request target_type")

        # Convert to DataFrame
        feature_df = pd.DataFrame(request.features)
        
        # Ensure candidate_number is string
        if "candidate_number" in feature_df.columns:
            feature_df["candidate_number"] = feature_df["candidate_number"].astype(str)

        try:
            predictions_df = predict_probabilities(
                trained_model,
                feature_df,
                target_date=request.target_date,
                top_k=request.top_k,
            )
        except ValueError as e:
            raise HTTPException(status_code=400, detail=str(e))

        # Ensure candidate_number is preserved as string
        predictions_df["candidate_number"] = predictions_df["candidate_number"].astype(str)

        # Drop labels and hit_counts if present
        output_cols = ["candidate_number", "probability", "rank"]
        compact_preds = predictions_df[output_cols].to_dict(orient="records")

        return {
            "target_date": request.target_date,
            "target_type": request.target_type,
            "model_name": trained_model["model_name"],
            "predictions": compact_preds,
        }

except ImportError:
    router = None  # type: ignore
