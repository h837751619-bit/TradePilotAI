from fastapi.testclient import TestClient

from tradepilot.api import create_app


def test_workflow_creates_trace_and_trace_api_lists_steps() -> None:
    client = TestClient(create_app("sqlite:///:memory:"))
    response = client.post(
        "/api/workflow/inquiry-to-quote",
        json={"inquiry": "We need 120 aluminum outdoor chairs for a hotel project in Germany."},
    )
    assert response.status_code == 200
    run_id = response.json()["run_id"]

    traces = client.get("/api/agent-runs").json()
    assert traces[0]["run_id"] == run_id
    assert [step["name"] for step in traces[0]["steps"]] == [
        "Inquiry parsed", "Product search", "Inventory and pricing", "Quote generated", "Human approval",
    ]
