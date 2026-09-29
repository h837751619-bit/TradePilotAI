from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_customer_search_api() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/customers", params={"q": "Acme"})
    assert response.status_code == 200
    assert response.json()[0]["company_name"] == "Acme Hotels"


def test_workflow_returns_customer_match_status() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.", "customer_name": "Acme Hotels"},
    )
    assert response.status_code == 200
    assert response.json()["customer"]["matched"] is True
