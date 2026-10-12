from tradepilot.ai_provider import AIProvider, AIResponse
from tradepilot.inquiry import parse_inquiry_with_provider


class FakeProvider(AIProvider):
    def complete(self, prompt: str) -> AIResponse:
        return AIResponse('{"quantity": 75, "destination_country": "France", "project_type": "resort", "product_keywords": ["outdoor sofa"]}', "fake", "test")


def test_provider_can_enrich_inquiry_requirements() -> None:
    result = parse_inquiry_with_provider("Need furniture", FakeProvider())
    assert result.quantity == 75
    assert result.destination_country == "France"
    assert result.product_keywords == ["outdoor sofa"]
    assert result.project_type == "resort"


def test_provider_failure_falls_back_to_rules() -> None:
    class BrokenProvider(AIProvider):
        def complete(self, prompt: str) -> AIResponse:
            raise OSError("Ollama unavailable")

    result = parse_inquiry_with_provider("Need 50 outdoor chairs in Germany", BrokenProvider())
    assert result.quantity == 50
    assert result.destination_country == "Germany"


def test_provider_accepts_markdown_and_string_keywords() -> None:
    class MarkdownProvider(AIProvider):
        def complete(self, prompt: str) -> AIResponse:
            return AIResponse('```json\n{"quantity": 80, "product_keywords": "outdoor chairs"}\n```', "fake", "test")

    result = parse_inquiry_with_provider("Need furniture", MarkdownProvider())
    assert result.quantity == 80
    assert "outdoor chairs" in result.product_keywords
