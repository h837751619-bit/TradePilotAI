from __future__ import annotations

import json
from dataclasses import dataclass
from urllib.request import Request, urlopen


@dataclass(frozen=True)
class AIResponse:
    text: str
    provider: str
    model: str


class AIProvider:
    name = "base"

    def complete(self, prompt: str) -> AIResponse:
        raise NotImplementedError


def parse_json_object(text: str) -> dict:
    """Parse a JSON object from a model response with optional prose/fences."""
    raw = text.strip().replace("```json", "").replace("```", "").strip()
    try:
        data = json.loads(raw)
    except json.JSONDecodeError:
        start, end = raw.find("{"), raw.rfind("}")
        if start < 0 or end <= start:
            raise
        data = json.loads(raw[start : end + 1])
    if not isinstance(data, dict):
        raise TypeError("AI response must be a JSON object")
    return data


class RuleBasedProvider(AIProvider):
    name = "rules"

    def __init__(self, model: str = "rules-v1") -> None:
        self.model = model

    def complete(self, prompt: str) -> AIResponse:
        return AIResponse(text=prompt, provider=self.name, model=self.model)


class OllamaProvider(AIProvider):
    name = "ollama"

    def __init__(
        self,
        base_url: str = "http://127.0.0.1:11434",
        model: str = "qwen3:8b",
        timeout: float = 30.0,
        think: bool | None = None,
    ) -> None:
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout
        self.think = think

    def complete(self, prompt: str) -> AIResponse:
        request_payload = {"model": self.model, "prompt": prompt, "stream": False}
        if self.think is not None:
            request_payload["think"] = self.think
        payload = json.dumps(request_payload).encode()
        request = Request(f"{self.base_url}/api/generate", data=payload, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode())
        return AIResponse(text=result.get("response", ""), provider=self.name, model=self.model)


class OpenAICompatibleProvider(AIProvider):
    """Chat completions provider for services implementing the OpenAI API shape."""

    name = "openai_compatible"

    def __init__(
        self,
        api_key: str,
        base_url: str = "https://api.openai.com/v1",
        model: str = "gpt-4o-mini",
        timeout: float = 45.0,
    ) -> None:
        self.api_key = api_key.strip()
        self.base_url = base_url.rstrip("/")
        self.model = model
        self.timeout = timeout

    def complete(self, prompt: str) -> AIResponse:
        if not self.api_key:
            raise ValueError("OpenAI-compatible API key is not configured")
        payload = json.dumps({
            "model": self.model,
            "messages": [{"role": "user", "content": prompt}],
            "stream": False,
        }).encode()
        request = Request(
            f"{self.base_url}/chat/completions",
            data=payload,
            headers={
                "Authorization": f"Bearer {self.api_key}",
                "Content-Type": "application/json",
            },
        )
        with urlopen(request, timeout=self.timeout) as response:
            result = json.loads(response.read().decode())
        content = result["choices"][0]["message"]["content"]
        if not isinstance(content, str):
            raise TypeError("Model response content must be text")
        return AIResponse(text=content, provider=self.name, model=self.model)
