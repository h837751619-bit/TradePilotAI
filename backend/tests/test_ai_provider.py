import json
from unittest.mock import patch

from tradepilot.ai_provider import OllamaProvider, RuleBasedProvider, parse_json_object
from tradepilot.auth import hash_password, issue_token, verify_password, verify_token


def test_rule_provider_returns_safe_response() -> None:
    result = RuleBasedProvider().complete("hello")
    assert result.provider == "rules"
    assert result.text == "hello"


def test_ollama_provider_uses_configured_qwen_model() -> None:
    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return json.dumps({"response": "ok"}).encode()

    with patch("tradepilot.ai_provider.urlopen", return_value=Response()) as request:
        result = OllamaProvider(model="qwen3:8b").complete("hello")
    assert result.text == "ok"
    assert result.model == "qwen3:8b"
    assert request.call_args.kwargs["timeout"] == 30.0


def test_ollama_provider_can_disable_thinking() -> None:
    class Response:
        def __enter__(self): return self
        def __exit__(self, *_): return False
        def read(self): return json.dumps({"response": "ok"}).encode()

    with patch("tradepilot.ai_provider.urlopen", return_value=Response()) as request:
        OllamaProvider(model="qwen3:8b", think=False).complete("hello")
    payload = json.loads(request.call_args.args[0].data.decode())
    assert payload["think"] is False


def test_parse_json_object_accepts_prose_and_markdown() -> None:
    result = parse_json_object('Here is the result:\n```json\n{"tags":["chair"]}\n```')
    assert result == {"tags": ["chair"]}


def test_auth_token_round_trip_and_tamper_rejection() -> None:
    token = issue_token("qa-reviewer", "test-secret", 60)
    assert verify_token(token, "test-secret") == "qa-reviewer"
    assert verify_token(token + "x", "test-secret") is None


def test_password_hash_round_trip_and_wrong_password_rejection() -> None:
    encoded = hash_password("correct-password")
    assert verify_password("correct-password", encoded)
    assert not verify_password("wrong-password", encoded)
