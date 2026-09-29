from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_complete_inquiry_to_approval_api_flow() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    inquiry = "We need 120 aluminum outdoor chairs for a hotel project in Germany."

    workflow = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": inquiry, "customer_name": "Acme Hotels"},
    )
    assert workflow.status_code == 200
    payload = workflow.json()
    assert payload["customer"]["matched"] is True
    assert payload["quote"]["sku"] == "NOVA-CHAIR-001"

    quote_id = payload["quote"]["id"]
    run_id = payload["run_id"]
    assert client.get("/api/customers?q=Acme").json()[0]["company_name"] == "Acme Hotels"
    assert client.get("/api/quotes").json()[0]["id"] == quote_id
    assert client.get("/api/agent-runs").json()[0]["run_id"] == run_id

    approval = client.post(f"/api/quotes/{quote_id}/approve")
    assert approval.status_code == 200
    assert approval.json() == {"id": quote_id, "status": "approved"}
    assert client.get("/api/quotes").json()[0]["status"] == "approved"
