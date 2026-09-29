from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_approval_api_persists_approved_status() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.", "customer_name": "Acme Hotels"},
    ).json()
    quote_id = created["quote"]["id"]

    response = client.post(f"/api/quotes/{quote_id}/approve")
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert client.get("/api/quotes").json()[0]["status"] == "approved"


def test_approval_api_rejects_unknown_quote() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post("/api/quotes/999/approve")
    assert response.status_code == 404
