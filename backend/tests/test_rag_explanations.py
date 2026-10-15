from tradepilot.ai_provider import AIProvider, AIResponse
from tradepilot.models import Product
from tradepilot.rag.explanations import (
    attach_ai_explanations,
    explain_product_candidates,
)
from tradepilot.seed import seed_products


class ExplanationProvider(AIProvider):
    def complete(self, prompt: str) -> AIResponse:
        assert "Use only facts in CANDIDATES" in prompt
        assert "NOVA-CHAIR-001" in prompt
        return AIResponse(
            '{"matches":['
            '{"sku":"NOVA-CHAIR-001","explanation":"Its aluminum construction and hotel use fit the request.",'
            '"evidence_fields":["material","description","not_a_field"]},'
            '{"sku":"INVENTED-SKU","explanation":"Invented product","evidence_fields":["material"]}'
            "]}",
            "fake",
            "grounded-test",
        )


def test_grounded_explanation_uses_database_evidence_and_rejects_unknown_sku(session) -> None:
    seed_products(session)
    candidates = [{"sku": "NOVA-CHAIR-001", "reasons": ["Semantic match 0.80"]}]
    explanations, provider, model = explain_product_candidates(
        session, "Need weatherproof hotel seating", candidates, ExplanationProvider()
    )
    attach_ai_explanations(candidates, explanations)

    product = session.query(Product).filter_by(sku="NOVA-CHAIR-001").one()
    assert provider == "fake"
    assert model == "grounded-test"
    assert "INVENTED-SKU" not in explanations
    assert candidates[0]["explanation"].startswith("Nova Aluminum Outdoor Chair matches based on")
    assert candidates[0]["model_explanation"].startswith("Its aluminum")
    assert candidates[0]["evidence"] == [
        {"field": "material", "value": product.material},
        {"field": "description", "value": product.description},
    ]
