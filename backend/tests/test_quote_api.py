from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_workflow_persists_quote_and_quote_list_returns_it() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
            "customer_name": "Acme Hotels",
        },
    )
    assert created.status_code == 200

    response = client.get("/api/quotes")
    assert response.status_code == 200
    quotes = response.json()
    assert len(quotes) == 1
    assert quotes[0]["customer_name"] == "Acme Hotels"
    assert quotes[0]["sku"] == "NOVA-CHAIR-001"
    assert quotes[0]["status"] == "draft"
