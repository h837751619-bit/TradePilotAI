from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_ai_settings_redacts_api_keys():
    client = TestClient(create_app("sqlite:///:memory:"))

    response = client.get("/api/settings/ai")

    assert response.status_code == 200
    body = response.json()
    assert body["api_key_storage"] == "runtime_only"
    assert {item["id"] for item in body["providers"]} == {"rules", "ollama", "openai_compatible", "deepseek", "kimi"}
    assert all("api_key" not in item for item in body["providers"])
    assert all(isinstance(item["api_key_configured"], bool) for item in body["providers"])


def test_ai_settings_can_switch_to_rules_without_secret():
    client = TestClient(create_app("sqlite:///:memory:"))

    response = client.patch("/api/settings/ai", json={"provider": "rules"})

    assert response.status_code == 200
    assert response.json()["active"] == "rules"


def test_ai_connection_test_for_rules_is_successful():
    client = TestClient(create_app("sqlite:///:memory:"))

    response = client.post("/api/settings/ai/test", json={"provider": "rules"})

    assert response.status_code == 200
    assert response.json()["success"] is True
    assert response.json()["model"] == "rules-v1"


def test_ai_diagnostics_reports_infrastructure_without_secrets():
    client = TestClient(create_app("sqlite:///:memory:"))

    response = client.get("/api/settings/ai/diagnostics")

    assert response.status_code == 200
    body = response.json()
    assert body["active"] in {"rules", "ollama"}
    checks = {item["id"]: item for item in body["checks"]}
    assert checks["mysql"]["status"] == "ok"
    assert checks["qdrant"]["status"] in {"disabled", "ok", "error"}
    assert all("api_key" not in item for item in body["checks"])
