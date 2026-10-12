from fastapi.testclient import TestClient

from tradepilot.api import create_app
from tradepilot.customer import extract_customer_name


def test_extract_customer_name_from_inquiry() -> None:
    assert extract_customer_name("Acme Hotels needs 120 outdoor chairs for Germany.") == "Acme Hotels"
    assert extract_customer_name("Please quote for Acme Hotels from Germany.") == "Acme Hotels"


def test_customer_search_api() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/customers", params={"q": "Acme"})
    assert response.status_code == 200
    assert response.json()[0]["company_name"] == "Acme Hotels"


def test_customer_crud_and_quote_history_api() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post("/api/customers", json={"company_name": "Blue Harbor", "contact_name": "Mia Chen", "country": "Italy", "email": "mia@blue-harbor.example"})
    assert created.status_code == 201
    customer_id = created.json()["id"]

    updated = client.patch(f"/api/customers/{customer_id}", json={"country": "France"})
    assert updated.status_code == 200
    assert updated.json()["country"] == "France"

    history = client.get(f"/api/customers/{customer_id}/quotes")
    assert history.status_code == 200
    assert history.json() == []

    deleted = client.delete(f"/api/customers/{customer_id}")
    assert deleted.status_code == 204
    assert client.get(f"/api/customers/{customer_id}").status_code == 404


def test_workflow_returns_customer_match_status() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.", "customer_name": "Acme Hotels"},
    )
    assert response.status_code == 200
    assert response.json()["customer"]["matched"] is True


def test_workflow_extracts_customer_name_when_not_provided() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    client.post("/api/ai/providers", json={"provider": "rules"})
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "Acme Hotels needs 120 aluminum outdoor chairs for a hotel project in Germany."},
    )
    assert response.status_code == 200
    assert response.json()["customer"]["matched"] is True
    assert response.json()["customer"]["company_name"] == "Acme Hotels"
