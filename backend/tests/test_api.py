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
    assert len(response.json()) == 6


def test_products_endpoint_validates_limit() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/products", params={"limit": 0})
    assert response.status_code == 422


def test_products_endpoint_supports_keyword_search() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/products", params={"q": "sofa"})
    assert response.status_code == 200
    assert response.json()[0]["sku"] == "NOVA-SOFA-001"


def test_products_endpoint_exposes_expanded_catalog_search_and_inventory() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.get("/api/products", params={"q": "teak extendable"})
    assert response.status_code == 200
    product = next(item for item in response.json() if item["sku"] == "NOVA-TABLE-003")
    assert product["available_quantity"] == 36
    assert product["unit_price_usd"] == 395.0


def test_rag_playground_rules_mode_is_read_only() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/rag/playground",
        json={
            "inquiry": "We need 50 aluminum outdoor chairs for a hotel project in China.",
            "mode": "rules",
            "top_k": 3,
            "score_threshold": 0.45,
        },
    )
    assert response.status_code == 200
    body = response.json()
    assert body["retrieval_mode"] == "rules"
    assert body["parsed"]["quantity"] == 50
    assert body["candidates"]
    assert body["timings"]["total_ms"] >= 0
    assert client.get("/api/quotes").json() == []


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


def test_inquiry_workflow_returns_grounded_product_explanation() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    client.post("/api/ai/providers", json={"provider": "ollama"})
    fake = type("FakeOllama", (), {})()

    def complete(prompt):
        if "CANDIDATES:" in prompt:
            return AIResponse(
                '{"matches":[{"sku":"NOVA-CHAIR-001",'
                '"explanation":"The catalog identifies it as a stackable aluminum hotel chair.",'
                '"evidence_fields":["description","material"]}]}',
                "ollama",
                "qwen3:8b",
            )
        return AIResponse(
            '{"quantity":50,"project_type":"hotel","product_keywords":["outdoor chair"]}',
            "ollama",
            "qwen3:8b",
        )

    fake.complete = complete
    with patch("tradepilot.api.OllamaProvider", return_value=fake):
        response = client.post(
            "/api/workflow/inquiry-to-quote",
            json={"inquiry": "We need 50 outdoor chairs for a hotel."},
        )
    assert response.status_code == 200
    payload = response.json()
    assert payload["explanation_mode"] == "grounded_ai"
    assert payload["explanation_provider"] == "ollama"
    chair = next(item for item in payload["product_matches"] if item["sku"] == "NOVA-CHAIR-001")
    assert chair["explanation"].startswith("Nova Aluminum Outdoor Chair matches based on")
    assert chair["model_explanation"].startswith("The catalog")
    assert [item["field"] for item in chair["evidence"]] == ["description", "material"]


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


def test_rag_evaluation_run_is_persisted_and_history_is_readable() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    run = client.post("/api/evaluation/rag/run", params={"mode": "rules"})
    assert run.status_code == 200
    payload = run.json()
    assert payload["id"] > 0
    assert payload["mode"] == "rules"
    assert payload["mrr"] == 0.9114583333333333
    history = client.get("/api/evaluation/rag/history")
    assert history.status_code == 200
    assert history.json()[0]["id"] == payload["id"]
    assert history.json()[0]["created_at"]
