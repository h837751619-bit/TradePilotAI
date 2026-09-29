from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_workflow_api_returns_quote_and_requirements() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
            "customer_name": "Acme Hotels",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["inquiry"]["quantity"] == 120
    assert payload["quote"]["sku"] == "NOVA-CHAIR-001"
    assert payload["quote"]["status"] == "draft"
    assert payload["risk"]["requires_approval"] is True


def test_workflow_api_rejects_missing_quantity() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "Please send your catalog."},
    )
    assert response.status_code == 422
