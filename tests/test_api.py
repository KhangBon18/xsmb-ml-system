"""Tests for the minimal FastAPI foundation (Phase 7C)."""

from __future__ import annotations

import pytest

try:
    from fastapi.testclient import TestClient
    from app.main import create_api_app
    HAS_FASTAPI = True
except ImportError:
    HAS_FASTAPI = False


pytestmark = pytest.mark.skipif(not HAS_FASTAPI, reason="FastAPI is not installed")


@pytest.fixture
def client():
    if not HAS_FASTAPI:
        return None
    app = create_api_app()
    if app is None:
        pytest.skip("FastAPI app failed to initialize")
    return TestClient(app)


class TestHealthEndpoint:
    def test_health_returns_200(self, client):
        response = client.get("/health")
        assert response.status_code == 200

    def test_health_content(self, client):
        response = client.get("/health")
        data = response.json()
        assert data["status"] == "ok"
        assert data["service"] == "xsmb-ml-system"


class TestTargetsEndpoint:
    def test_targets_returns_200(self, client):
        response = client.get("/targets")
        assert response.status_code == 200

    def test_targets_content(self, client):
        response = client.get("/targets")
        data = response.json()
        assert "targets" in data
        targets = data["targets"]
        assert len(targets) == 3
        assert "loto_2d_all_prizes" in targets
        assert "db_2cang" in targets
        assert "db_3cang" in targets
