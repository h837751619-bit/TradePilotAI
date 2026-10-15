from __future__ import annotations

from collections.abc import Sequence


class ProductReranker:
    """Optional lazy Cross-Encoder reranker for a small candidate set."""

    def __init__(self, model_name: str, enabled: bool = False) -> None:
        self.model_name = model_name
        self.enabled = enabled
        self._model = None

    @property
    def model(self):
        if self._model is None:
            from fastembed import TextCrossEncoder

            self._model = TextCrossEncoder(model_name=self.model_name)
        return self._model

    def score(self, query: str, documents: Sequence[str]) -> list[float]:
        if not self.enabled or not documents:
            return []
        values = self.model.rerank(query, list(documents))
        return [float(value) for value in values]
