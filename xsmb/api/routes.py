"""FastAPI routes for XSMB ML system."""

from __future__ import annotations

from xsmb.config import TARGET_TYPES

try:
    from fastapi import APIRouter
    from xsmb.api.schemas import HealthResponse, TargetsResponse
    
    router = APIRouter()

    @router.get("/health", response_model=HealthResponse)
    def health_check() -> dict[str, str]:
        return {"status": "ok", "service": "xsmb-ml-system"}

    @router.get("/targets", response_model=TargetsResponse)
    def get_targets() -> dict[str, list[str]]:
        return {"targets": list(TARGET_TYPES)}
except ImportError:
    router = None  # type: ignore
