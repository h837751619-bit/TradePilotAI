from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_evaluation_api_returns_metrics() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/evaluation")
    assert response.status_code == 200
    assert response.json()["cases"] == 6
    assert response.json()["failure_detection_rate"] == 1.0
