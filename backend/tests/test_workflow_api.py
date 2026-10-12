from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_workflow_api_returns_match_preview_without_persisting_quote() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 50  chairs for a hotel project in China.",
            "customer_name": "Acme Hotels",
        },
    )
    assert response.status_code == 200
    payload = response.json()
    assert payload["inquiry"]["quantity"] == 50
    assert payload["inquiry"]["destination_country"] == "China"
    assert payload["quote"]["sku"] == "NOVA-CHAIR-001"
    assert payload["quote"]["id"] is None
    assert payload["quote"]["status"] == "pending_selection"
    assert payload["risk"]["requires_approval"] is False
    assert client.get("/api/quotes").json() == []


def test_workflow_api_rejects_missing_quantity() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "Please send your catalog."},
    )
    assert response.status_code == 422


def test_workflow_api_can_quote_selected_candidate() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 40 aluminum outdoor chairs for a hotel project in Germany.",
            "customer_name": "Acme Hotels",
            "selected_sku": "NOVA-SOFA-001",
        },
    )
    assert response.status_code == 200
    assert response.json()["quote"]["sku"] == "NOVA-SOFA-001"


def test_workflow_api_uses_budget_and_lead_time_for_auto_selection() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany. Budget under $50 within 40 days.",
            "customer_name": "Acme Hotels",
        },
    )
    assert response.status_code == 200
    assert response.json()["quote"]["sku"] == "NOVA-CHAIR-001"
    assert response.json()["quote"]["status"] == "pending_selection"
