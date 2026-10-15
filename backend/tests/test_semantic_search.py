from unittest.mock import patch

from fastapi.testclient import TestClient

from tradepilot.api import create_app
from tradepilot.config import Settings
from tradepilot.rag.vector_store import ProductVectorStore


def test_semantic_retrieval_finds_product_without_known_keyword() -> None:
    settings = Settings(ai_provider="rules", semantic_search_enabled=True)
    with patch("tradepilot.api.get_settings", return_value=settings), patch.object(
        ProductVectorStore, "search", return_value={"NOVA-CHAIR-001": 0.87}
    ):
        client = TestClient(create_app("sqlite:///:memory:"))
        response = client.post(
            "/api/workflow/inquiry-to-quote",
            json={"inquiry": "Need 50 weatherproof seats for a seaside property."},
        )
    assert response.status_code == 200
    result = response.json()
    assert result["retrieval_mode"] == "semantic"
    assert result["quote"]["sku"] == "NOVA-CHAIR-001"
    assert result["quote"]["id"] is None
    assert "Semantic match" in result["product_matches"][0]["reasons"][0]


def test_semantic_service_failure_uses_rule_matching() -> None:
    settings = Settings(ai_provider="rules", semantic_search_enabled=True)
    with patch("tradepilot.api.get_settings", return_value=settings), patch.object(
        ProductVectorStore, "search", side_effect=OSError("index offline")
    ):
        client = TestClient(create_app("sqlite:///:memory:"))
        response = client.post(
            "/api/workflow/inquiry-to-quote",
            json={"inquiry": "Need 50 outdoor chairs for a hotel."},
        )
    assert response.status_code == 200
    assert response.json()["retrieval_mode"] == "rules_fallback"


def test_rebuild_indexes_existing_products() -> None:
    settings = Settings(ai_provider="rules", semantic_search_enabled=True)
    with patch("tradepilot.api.get_settings", return_value=settings), patch.object(
        ProductVectorStore, "rebuild", return_value=5
    ) as rebuild:
        client = TestClient(create_app("sqlite:///:memory:"))
        response = client.post("/api/products/rebuild-semantic-index")
    assert response.status_code == 200
    assert response.json()["indexed_products"] == 5
    rebuild.assert_called_once()


def test_huggingface_embedding_uses_e5_query_and_passage_prefixes() -> None:
    class FakeVector:
        def tolist(self):
            return [0.2, 0.4]

    class FakeModel:
        def __init__(self):
            self.inputs = []

        def embed(self, texts):
            self.inputs.extend(texts)
            return iter([FakeVector()])

    model = FakeModel()
    store = ProductVectorStore(
        "http://localhost:11434", "http://localhost:6333",
        "intfloat/multilingual-e5-small", "products",
    )
    store.__dict__["local_model"] = model
    assert store.embed("aluminum chair") == [0.2, 0.4]
    assert store.embed("hotel seating", is_query=True) == [0.2, 0.4]
    assert model.inputs == ["passage: aluminum chair", "query: hotel seating"]
