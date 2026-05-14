"""Pydantic schemas for the FastAPI endpoints."""

from __future__ import annotations

from typing import Any, List, Optional

try:
    from pydantic import BaseModel
except ImportError:
    # Fallback if pydantic is not installed
    class BaseModel:  # type: ignore
        pass

class HealthResponse(BaseModel):
    status: str
    service: str

class TargetsResponse(BaseModel):
    targets: List[str]

class BacktestHistoryRow(BaseModel):
    draw_date: str
    target_type: str
    candidate_number: str
    label: int
    hit_count: int

class BacktestRequest(BaseModel):
    target_type: str
    model_name: str
    start_date: Optional[str] = None
    end_date: Optional[str] = None
    min_history_days: int = 30
    top_k_values: List[int] = [5, 10, 20]
    history: List[BacktestHistoryRow]

class BacktestResponse(BaseModel):
    target_type: str
    model_name: str
    summary: dict[str, Any]
    prediction_count: int
