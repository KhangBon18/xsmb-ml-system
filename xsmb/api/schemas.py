"""Pydantic schemas for the FastAPI endpoints."""

from __future__ import annotations

from typing import List

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
