from fastapi.testclient import TestClient

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
