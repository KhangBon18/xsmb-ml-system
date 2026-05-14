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


def _make_history_payload(num_dates: int = 35, target_type: str = "loto_2d_all_prizes", include_008: bool = False) -> list[dict[str, str | int]]:
    from datetime import date, timedelta
    base = date(2024, 1, 1)
    rows = []
    candidates = ["00", "05", "10", "55"]
    if include_008:
        candidates.append("008")
    for day_offset in range(num_dates):
        draw_date = (base + timedelta(days=day_offset)).isoformat()
        for candidate in candidates:
            label = 1 if (int(candidate) % 10) == (day_offset % 10) else 0
            rows.append({
                "draw_date": draw_date,
                "target_type": target_type,
                "candidate_number": candidate,
                "label": label,
                "hit_count": label,
            })
    return rows


class TestBacktestEndpoint:
    def test_backtest_returns_200_and_summary(self, client):
        payload = {
            "target_type": "loto_2d_all_prizes",
            "model_name": "frequency_30",
            "history": _make_history_payload(num_dates=35)
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["target_type"] == "loto_2d_all_prizes"
        assert data["model_name"] == "frequency_30"
        assert "summary" in data
        assert "brier_score" in data["summary"]
        assert "prediction_count" in data
        assert data["prediction_count"] > 0

    def test_backtest_leading_zero_preservation(self, client):
        payload = {
            "target_type": "db_3cang",
            "model_name": "frequency_30",
            "history": _make_history_payload(num_dates=35, target_type="db_3cang", include_008=True)
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code == 200

    def test_backtest_missing_history_returns_422(self, client):
        payload = {
            "target_type": "loto_2d_all_prizes",
            "model_name": "frequency_30"
            # Missing history
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code == 422

    def test_backtest_empty_history_returns_400(self, client):
        payload = {
            "target_type": "loto_2d_all_prizes",
            "model_name": "frequency_30",
            "history": []
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code in (400, 422)

    def test_backtest_invalid_target_type(self, client):
        payload = {
            "target_type": "invalid_type",
            "model_name": "frequency_30",
            "history": _make_history_payload(num_dates=5)
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code in (400, 422)

    def test_backtest_invalid_model_name(self, client):
        payload = {
            "target_type": "loto_2d_all_prizes",
            "model_name": "invalid_model",
            "history": _make_history_payload(num_dates=5)
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code in (400, 422)

    def test_backtest_invalid_top_k_values(self, client):
        payload = {
            "target_type": "loto_2d_all_prizes",
            "model_name": "frequency_30",
            "top_k_values": [5, -1, 10],
            "history": _make_history_payload(num_dates=5)
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code in (400, 422)

    def test_backtest_invalid_min_history_days(self, client):
        payload = {
            "target_type": "loto_2d_all_prizes",
            "model_name": "frequency_30",
            "min_history_days": 0,
            "history": _make_history_payload(num_dates=5)
        }
        response = client.post("/backtest", json=payload)
        assert response.status_code in (400, 422)


def _make_feature_payload(num_dates: int = 10, target_type: str = "loto_2d_all_prizes", include_008: bool = False) -> list[dict[str, str | int | float]]:
    from datetime import date, timedelta
    base = date(2024, 1, 1)
    rows = []
    candidates = ["00", "05", "10", "55"]
    if include_008:
        candidates.append("008")
    for day_offset in range(num_dates):
        target_date = (base + timedelta(days=day_offset)).isoformat()
        for idx, candidate in enumerate(candidates):
            label = 1 if (idx % 10) == (day_offset % 10) else 0
            row = {
                "target_date": target_date,
                "target_type": target_type,
                "candidate_number": candidate,
                "label": label,
                "hit_count": label,
                "freq_30": (idx + day_offset) % 30,
                "current_gap": idx + 1,
                "rolling_hit_rate_30": 0.05,
            }
            rows.append(row)
    return rows


@pytest.fixture
def trained_artifact(tmp_path):
    if not HAS_FASTAPI:
        return None
    from xsmb.models.train import train_model, save_model_artifact
    import pandas as pd
    features = _make_feature_payload(num_dates=10, target_type="loto_2d_all_prizes")
    df = pd.DataFrame(features)
    df["candidate_number"] = df["candidate_number"].astype(str)
    trained = train_model(df, target_type="loto_2d_all_prizes", model_name="logistic_regression")
    return save_model_artifact(trained, str(tmp_path))


@pytest.fixture
def trained_db3_artifact(tmp_path):
    if not HAS_FASTAPI:
        return None
    from xsmb.models.train import train_model, save_model_artifact
    import pandas as pd
    features = _make_feature_payload(num_dates=10, target_type="db_3cang", include_008=True)
    df = pd.DataFrame(features)
    df["candidate_number"] = df["candidate_number"].astype(str)
    trained = train_model(df, target_type="db_3cang", model_name="logistic_regression")
    return save_model_artifact(trained, str(tmp_path))


class TestPredictEndpoint:
    def test_predict_returns_200(self, client, trained_artifact):
        features = _make_feature_payload(num_dates=1, target_type="loto_2d_all_prizes")
        payload = {
            "target_date": "2024-01-01",
            "target_type": "loto_2d_all_prizes",
            "top_k": 20,
            "artifact_path": trained_artifact,
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert data["target_date"] == "2024-01-01"
        assert data["target_type"] == "loto_2d_all_prizes"
        assert data["model_name"] == "logistic_regression"
        
        preds = data["predictions"]
        assert len(preds) > 0
        for p in preds:
            assert "candidate_number" in p
            assert "probability" in p
            assert "rank" in p
            assert 0.0 <= p["probability"] <= 1.0
            assert isinstance(p["candidate_number"], str)
            
        candidate_numbers = {p["candidate_number"] for p in preds}
        assert "00" in candidate_numbers
        assert "05" in candidate_numbers

    def test_predict_leading_zero_db3cang(self, client, trained_db3_artifact):
        features = _make_feature_payload(num_dates=1, target_type="db_3cang", include_008=True)
        payload = {
            "target_date": "2024-01-01",
            "target_type": "db_3cang",
            "top_k": 20,
            "artifact_path": trained_db3_artifact,
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        preds = data["predictions"]
        candidate_numbers = {p["candidate_number"] for p in preds}
        assert "008" in candidate_numbers

    def test_predict_top_k(self, client, trained_artifact):
        features = _make_feature_payload(num_dates=1, target_type="loto_2d_all_prizes")
        payload = {
            "target_date": "2024-01-01",
            "target_type": "loto_2d_all_prizes",
            "top_k": 2,
            "artifact_path": trained_artifact,
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 200
        data = response.json()
        assert len(data["predictions"]) == 2

    def test_predict_missing_artifact(self, client):
        features = _make_feature_payload(num_dates=1, target_type="loto_2d_all_prizes")
        payload = {
            "target_date": "2024-01-01",
            "target_type": "loto_2d_all_prizes",
            "top_k": 20,
            # missing artifact_path
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 422

    def test_predict_nonexistent_artifact(self, client):
        features = _make_feature_payload(num_dates=1, target_type="loto_2d_all_prizes")
        payload = {
            "target_date": "2024-01-01",
            "target_type": "loto_2d_all_prizes",
            "top_k": 20,
            "artifact_path": "/nonexistent/model.pkl",
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 400

    def test_predict_empty_features(self, client, trained_artifact):
        payload = {
            "target_date": "2024-01-01",
            "target_type": "loto_2d_all_prizes",
            "top_k": 20,
            "artifact_path": trained_artifact,
            "features": [],
        }
        response = client.post("/predict", json=payload)
        assert response.status_code in (400, 422)

    def test_predict_invalid_target_type(self, client, trained_artifact):
        features = _make_feature_payload(num_dates=1, target_type="loto_2d_all_prizes")
        payload = {
            "target_date": "2024-01-01",
            "target_type": "invalid_type",
            "top_k": 20,
            "artifact_path": trained_artifact,
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code in (400, 422)

    def test_predict_invalid_top_k(self, client, trained_artifact):
        features = _make_feature_payload(num_dates=1, target_type="loto_2d_all_prizes")
        payload = {
            "target_date": "2024-01-01",
            "target_type": "loto_2d_all_prizes",
            "top_k": -5,
            "artifact_path": trained_artifact,
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code in (400, 422)

    def test_predict_mismatched_target_type(self, client, trained_db3_artifact):
        # Artifact is db_3cang, but request says loto_2d_all_prizes
        features = _make_feature_payload(num_dates=1, target_type="loto_2d_all_prizes")
        payload = {
            "target_date": "2024-01-01",
            "target_type": "loto_2d_all_prizes",
            "top_k": 20,
            "artifact_path": trained_db3_artifact,
            "features": features,
        }
        response = client.post("/predict", json=payload)
        assert response.status_code == 400
