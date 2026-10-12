from unittest.mock import patch

from fastapi.testclient import TestClient

from tradepilot.api import create_app
from tradepilot.auth import hash_password
from tradepilot.config import Settings


def test_approval_api_persists_approved_status() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.", "customer_name": "Acme Hotels", "selected_sku": "NOVA-CHAIR-001"},
    ).json()
    quote_id = created["quote"]["id"]

    response = client.post(f"/api/quotes/{quote_id}/approve", headers={"X-Actor-Id": "qa-reviewer"})
    assert response.status_code == 200
    assert response.json()["status"] == "approved"
    assert client.get("/api/quotes").json()[0]["status"] == "approved"
    history = client.get(f"/api/quotes/{quote_id}").json()["approval_history"]
    assert history == [
        {
            "id": 1,
            "from_status": "draft",
            "to_status": "approved",
            "actor": "qa-reviewer",
            "created_at": history[0]["created_at"],
        }
    ]


def test_approval_api_rejects_unknown_quote() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post("/api/quotes/999/approve")
    assert response.status_code == 404


def test_enabled_auth_requires_login_and_records_token_subject() -> None:
    settings = Settings(
        auth_enabled=True,
        auth_secret="test-secret",
        auth_username="admin",
        auth_password_hash=hash_password("correct-password"),
    )
    with patch("tradepilot.api.get_settings", return_value=settings):
        client = TestClient(create_app("sqlite:///:memory:"))
        login = client.post("/api/auth/login", json={"username": "admin", "password": "correct-password"})
        assert login.status_code == 200
        token = login.json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/quotes").status_code == 401
        assert client.post(
            "/api/workflow/inquiry-to-quote",
            json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany."},
        ).status_code == 401
        created = client.post(
            "/api/workflow/inquiry-to-quote",
            json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.", "selected_sku": "NOVA-CHAIR-001"},
            headers=headers,
        ).json()
        quote_id = created["quote"]["id"]

        wrong_login = client.post("/api/auth/login", json={"username": "admin", "password": "wrong"})
        assert wrong_login.status_code == 401
        assert client.post(f"/api/quotes/{quote_id}/approve").status_code == 401
        assert client.post(f"/api/quotes/{quote_id}/cancel").status_code == 401
        assert client.get(f"/api/quotes/{quote_id}").status_code == 401

        token_data = login.json()
        refresh_token = token_data["refresh_token"]
        refreshed = client.post("/api/auth/refresh", json={"refresh_token": refresh_token})
        assert refreshed.status_code == 200
        assert client.post("/api/auth/refresh", json={"refresh_token": refresh_token}).status_code == 401
        token = refreshed.json()["access_token"]
        approved = client.post(
            f"/api/quotes/{quote_id}/approve",
            headers={"Authorization": f"Bearer {token}", "X-Actor-Id": "spoofed-user"},
        )
        assert approved.status_code == 200
        assert client.get(f"/api/quotes/{quote_id}", headers={"Authorization": f"Bearer {token}"}).json()["approval_history"][0]["actor"] == "admin"
        rotated_refresh = refreshed.json()["refresh_token"]
        assert client.post("/api/auth/logout", json={"refresh_token": rotated_refresh}).status_code == 200
        assert client.post("/api/auth/refresh", json={"refresh_token": rotated_refresh}).status_code == 401


def test_non_approver_role_cannot_approve() -> None:
    settings = Settings(
        auth_enabled=True,
        auth_secret="test-secret",
        auth_username="admin",
        auth_password_hash=hash_password("admin-password"),
        auth_role="admin",
    )
    with patch("tradepilot.api.get_settings", return_value=settings):
        client = TestClient(create_app("sqlite:///:memory:"))
        admin_token = client.post("/api/auth/login", json={"username": "admin", "password": "admin-password"}).json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        quote_id = client.post(
            "/api/workflow/inquiry-to-quote",
            json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.", "selected_sku": "NOVA-CHAIR-001"},
            headers=admin_headers,
        ).json()["quote"]["id"]
        client.post("/api/users", headers=admin_headers, json={"username": "viewer", "password": "viewer-password", "role": "viewer"})
        token = client.post("/api/auth/login", json={"username": "viewer", "password": "viewer-password"}).json()["access_token"]
        response = client.post(f"/api/quotes/{quote_id}/approve", headers={"Authorization": f"Bearer {token}"})
        assert response.status_code == 403
        assert client.post(f"/api/quotes/{quote_id}/cancel", headers={"Authorization": f"Bearer {token}"}).status_code == 403


def test_viewer_can_read_business_data_but_cannot_create_quotes_or_customers() -> None:
    settings = Settings(
        auth_enabled=True,
        auth_secret="test-secret",
        auth_username="viewer",
        auth_password_hash=hash_password("viewer-password"),
        auth_role="viewer",
    )
    with patch("tradepilot.api.get_settings", return_value=settings):
        client = TestClient(create_app("sqlite:///:memory:"))
        token = client.post("/api/auth/login", json={"username": "viewer", "password": "viewer-password"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.get("/api/customers").status_code == 401
        assert client.get("/api/agent-runs").status_code == 401
        assert client.get("/api/ai/providers").status_code == 401
        assert client.get("/api/products").status_code == 401
        assert client.get("/api/customers", headers=headers).status_code == 200
        assert client.get("/api/agent-runs", headers=headers).status_code == 200
        assert client.get("/api/ai/providers", headers=headers).status_code == 200
        assert client.get("/api/products", headers=headers).status_code == 200
        assert client.post("/api/ai/providers", headers=headers, json={"provider": "rules"}).status_code == 403
        assert client.post(
            "/api/workflow/inquiry-to-quote",
            headers=headers,
            json={"inquiry": "We need 20 outdoor chairs for a hotel."},
        ).status_code == 403
        assert client.post("/api/customers", headers=headers, json={"company_name": "Blocked Customer"}).status_code == 403


def test_deactivated_user_cannot_use_an_unexpired_access_token() -> None:
    settings = Settings(
        auth_enabled=True,
        auth_secret="test-secret",
        auth_username="admin",
        auth_password_hash=hash_password("admin-password"),
        auth_role="admin",
    )
    with patch("tradepilot.api.get_settings", return_value=settings):
        client = TestClient(create_app("sqlite:///:memory:"))
        admin_token = client.post("/api/auth/login", json={"username": "admin", "password": "admin-password"}).json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        quote_id = client.post(
            "/api/workflow/inquiry-to-quote",
            headers=admin_headers,
            json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany.", "selected_sku": "NOVA-CHAIR-001"},
        ).json()["quote"]["id"]
        created = client.post(
            "/api/users",
            headers=admin_headers,
            json={"username": "sales", "password": "sales-password", "role": "approver"},
        )
        sales_id = created.json()["id"]
        sales_token = client.post("/api/auth/login", json={"username": "sales", "password": "sales-password"}).json()["access_token"]
        assert client.patch(f"/api/users/{sales_id}", headers=admin_headers, json={"is_active": False}).status_code == 200
        response = client.post(f"/api/quotes/{quote_id}/approve", headers={"Authorization": f"Bearer {sales_token}"})
        assert response.status_code == 401


def test_viewer_cannot_change_product_catalog() -> None:
    settings = Settings(
        auth_enabled=True,
        auth_secret="test-secret",
        auth_username="viewer",
        auth_password_hash=hash_password("viewer-password"),
        auth_role="viewer",
    )
    with patch("tradepilot.api.get_settings", return_value=settings):
        client = TestClient(create_app("sqlite:///:memory:"))
        token = client.post("/api/auth/login", json={"username": "viewer", "password": "viewer-password"}).json()["access_token"]
        headers = {"Authorization": f"Bearer {token}"}
        assert client.patch("/api/products/NOVA-CHAIR-001", headers=headers, json={"material": "test"}).status_code == 403
        assert client.post(
            "/api/products",
            headers=headers,
            json={"sku": "TEST-001", "name": "Test", "category": "Test", "unit_price_usd": 1},
        ).status_code == 403
        assert client.delete("/api/products/NOVA-CHAIR-001", headers=headers).status_code == 403


def test_admin_can_manage_users_but_viewer_cannot() -> None:
    settings = Settings(
        auth_enabled=True,
        auth_secret="test-secret",
        auth_username="admin",
        auth_password_hash=hash_password("admin-password"),
        auth_role="admin",
    )
    with patch("tradepilot.api.get_settings", return_value=settings):
        client = TestClient(create_app("sqlite:///:memory:"))
        admin_token = client.post("/api/auth/login", json={"username": "admin", "password": "admin-password"}).json()["access_token"]
        admin_headers = {"Authorization": f"Bearer {admin_token}"}
        created = client.post("/api/users", headers=admin_headers, json={"username": "sales", "password": "sales-password", "role": "approver"})
        assert created.status_code == 201
        user_id = created.json()["id"]
        assert "password_hash" not in created.json()
        updated = client.patch(f"/api/users/{user_id}", headers=admin_headers, json={"role": "viewer", "is_active": False})
        assert updated.status_code == 200
        assert updated.json()["is_active"] is False
        self_deactivate = client.patch("/api/users/1", headers=admin_headers, json={"is_active": False})
        assert self_deactivate.status_code == 400
