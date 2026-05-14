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

except ImportError:
    router = None  # type: ignore
