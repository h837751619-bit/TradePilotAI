from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_workflow_persists_quote_and_quote_list_returns_it() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
            "customer_name": "Acme Hotels",
            "selected_sku": "NOVA-CHAIR-001",
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


def test_quote_detail_returns_risk_email_and_product_matches() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
            "customer_name": "Acme Hotels",
            "selected_sku": "NOVA-CHAIR-001",
        },
    ).json()

    response = client.get(f"/api/quotes/{created['quote']['id']}")

    assert response.status_code == 200
    detail = response.json()
    assert detail["risk"]["requires_approval"] is True
    assert "Quotation for 120 units" in detail["email"]["subject"]
    assert detail["product_matches"][0]["sku"] == "NOVA-CHAIR-001"


def test_repeating_same_workflow_does_not_create_duplicate_quote() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    payload = {
        "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
        "customer_name": "Acme Hotels",
        "selected_sku": "NOVA-CHAIR-001",
    }

    first = client.post("/api/workflow/inquiry-to-quote", json=payload)
    second = client.post("/api/workflow/inquiry-to-quote", json=payload)

    assert first.status_code == 200
    assert second.status_code == 200
    assert second.json()["quote"]["id"] == first.json()["quote"]["id"]
    assert len(client.get("/api/quotes").json()) == 1
