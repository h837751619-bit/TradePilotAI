from unittest.mock import patch

from fastapi.testclient import TestClient
from sqlalchemy import select
from sqlalchemy.dialects import mysql

from tradepilot.api import create_app
from tradepilot.auth import hash_password
from tradepilot.config import Settings
from tradepilot.inventory import Inventory
from tradepilot.models import QuoteRecord


def test_mysql_inventory_transition_queries_compile_with_row_locks() -> None:
    inventory_sql = str(select(Inventory).where(Inventory.sku == "SKU-1").with_for_update().compile(dialect=mysql.dialect()))
    quote_sql = str(select(QuoteRecord).where(QuoteRecord.id == 1).with_for_update().compile(dialect=mysql.dialect()))

    assert "FOR UPDATE" in inventory_sql
    assert "FOR UPDATE" in quote_sql


def test_selected_quote_reserves_then_approval_deducts_inventory() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
            "customer_name": "Acme Hotels",
            "selected_sku": "NOVA-CHAIR-001",
        },
    ).json()
    quote_id = created["quote"]["id"]

    product = next(item for item in client.get("/api/products").json() if item["sku"] == "NOVA-CHAIR-001")
    assert product["on_hand_quantity"] == 500
    assert product["reserved_quantity"] == 120
    assert product["available_quantity"] == 380

    assert client.post(f"/api/quotes/{quote_id}/approve").json()["status"] == "approved"
    movements = client.get(f"/api/quotes/{quote_id}").json()["inventory_movements"]
    assert [item["movement_type"] for item in movements] == ["reserve", "deduct"]
    assert all(item["quantity"] == 120 for item in movements)
    product = next(item for item in client.get("/api/products").json() if item["sku"] == "NOVA-CHAIR-001")
    assert product["on_hand_quantity"] == 380
    assert product["reserved_quantity"] == 0
    assert product["available_quantity"] == 380


def test_cancelled_quote_releases_inventory_reservation() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    quote_id = client.post(
        "/api/workflow/inquiry-to-quote",
        json={
            "inquiry": "We need 50 aluminum outdoor chairs for a hotel project in Germany.",
            "selected_sku": "NOVA-CHAIR-001",
        },
    ).json()["quote"]["id"]

    assert client.post(f"/api/quotes/{quote_id}/cancel").json()["status"] == "cancelled"
    movements = client.get(f"/api/quotes/{quote_id}").json()["inventory_movements"]
    assert [item["movement_type"] for item in movements] == ["reserve", "release"]
    product = next(item for item in client.get("/api/products").json() if item["sku"] == "NOVA-CHAIR-001")
    assert product["on_hand_quantity"] == 500
    assert product["reserved_quantity"] == 0


def test_product_library_can_edit_on_hand_inventory() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.patch("/api/products/NOVA-CHAIR-001/inventory", json={"on_hand_quantity": 777, "reason": "QA stock setup"}, headers={"X-Actor-Id": "qa-user"})

    assert response.status_code == 200
    assert response.json()["available_quantity"] == 777
    movement = client.get("/api/products/NOVA-CHAIR-001/inventory/movements").json()[0]
    assert movement["movement_type"] == "adjustment"
    assert movement["previous_quantity"] == 500
    assert movement["new_quantity"] == 777
    assert movement["reason"] == "QA stock setup"
    assert movement["actor"] == "qa-user"


def test_product_library_can_query_inventory_movements() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    quote_id = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "We need 50 aluminum outdoor chairs for a hotel project in Germany.", "selected_sku": "NOVA-CHAIR-001"},
    ).json()["quote"]["id"]
    movements = client.get("/api/products/NOVA-CHAIR-001/inventory/movements")
    assert movements.status_code == 200
    assert movements.json()[0]["quote_id"] == quote_id
    assert movements.json()[0]["movement_type"] == "reserve"


def test_inventory_edit_requires_approver_when_auth_is_enabled() -> None:
    settings = Settings(
        auth_enabled=True,
        auth_secret="test-secret",
        auth_username="viewer",
        auth_password_hash=hash_password("viewer-password"),
        auth_role="viewer",
    )
    with patch("tradepilot.api.get_settings", return_value=settings):
        client = TestClient(create_app("sqlite:///:memory:"))
        assert client.patch("/api/products/NOVA-CHAIR-001/inventory", json={"on_hand_quantity": 501}).status_code == 401
        token = client.post("/api/auth/login", json={"username": "viewer", "password": "viewer-password"}).json()["access_token"]
        response = client.patch(
            "/api/products/NOVA-CHAIR-001/inventory",
            headers={"Authorization": f"Bearer {token}"},
            json={"on_hand_quantity": 501},
        )
        assert response.status_code == 403
