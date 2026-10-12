from unittest.mock import patch

from fastapi.testclient import TestClient

from tradepilot.ai_provider import AIResponse
from tradepilot.api import create_app


def test_health_endpoint() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/health")
    assert response.status_code == 200
    assert response.json() == {"status": "ok"}


def test_products_endpoint_supports_filters() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/products", params={"category": "Outdoor Chair"})
    assert response.status_code == 200
    assert len(response.json()) == 1


def test_products_endpoint_validates_limit() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/products", params={"limit": 0})
    assert response.status_code == 422


def test_products_endpoint_supports_keyword_search() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/products", params={"q": "sofa"})
    assert response.status_code == 200
    assert response.json()[0]["sku"] == "NOVA-SOFA-001"


def test_product_update_endpoint_changes_catalog_data() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.patch("/api/products/NOVA-CHAIR-001", json={"unit_price_usd": 42.5, "min_order_quantity": 60})
    assert response.status_code == 200
    assert response.json()["unit_price_usd"] == 42.5
    assert response.json()["min_order_quantity"] == 60


def test_product_create_and_delete_endpoints() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    created = client.post("/api/products", json={"sku": "TEST-001", "name": "Test product", "category": "Test", "unit_price_usd": 10})
    assert created.status_code == 201
    deleted = client.delete("/api/products/TEST-001")
    assert deleted.status_code == 204
    assert client.get("/api/products", params={"q": "Test product"}).json() == []
    visible = client.get("/api/products", params={"q": "Test product", "include_inactive": "true"})
    assert visible.status_code == 200
    assert visible.json()[0]["is_active"] is False


def test_product_tag_suggestions_use_rules_when_selected() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    client.post("/api/ai/providers", json={"provider": "rules"})
    response = client.post("/api/products/NOVA-CHAIR-001/suggest-tags")
    assert response.status_code == 200
    assert response.json()["provider"] == "rules"
    assert response.json()["suggestions"]


def test_product_tag_suggestions_use_ollama_with_fast_json_mode() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    client.post("/api/ai/providers", json={"provider": "ollama"})
    fake = type("FakeOllama", (), {})()
    fake.complete = lambda prompt: AIResponse(
        'Here are tags:\n```json\n{"tags":["outdoor seating", "aluminum chair"]}\n```',
        "ollama",
        "qwen3:8b",
    )
    with patch("tradepilot.api.OllamaProvider", return_value=fake) as provider:
        response = client.post("/api/products/NOVA-CHAIR-001/suggest-tags")
    assert response.status_code == 200
    assert response.json()["suggestions"] == ["outdoor seating", "aluminum chair"]
    assert provider.call_args.kwargs["timeout"] == 90.0
    assert provider.call_args.kwargs["think"] is False


def test_inquiry_workflow_uses_fast_json_mode_for_ollama() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    client.post("/api/ai/providers", json={"provider": "ollama"})
    fake = type("FakeOllama", (), {})()
    fake.complete = lambda prompt: AIResponse(
        '{"quantity":120,"destination_country":"Germany","project_type":"hotel","product_keywords":["aluminum","outdoor chair"]}',
        "ollama",
        "qwen3:8b",
    )
    with patch("tradepilot.api.OllamaProvider", return_value=fake) as provider:
        response = client.post(
            "/api/workflow/inquiry-to-quote",
            json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany."},
        )
    assert response.status_code == 200
    assert provider.call_args.kwargs["think"] is False


def test_validation_errors_use_unified_shape() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/products", params={"limit": 0})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"


def test_cors_allows_local_frontend() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.options(
        "/api/products",
        headers={"Origin": "http://localhost:5173", "Access-Control-Request-Method": "GET"},
    )
    assert response.headers["access-control-allow-origin"] == "http://localhost:5173"
