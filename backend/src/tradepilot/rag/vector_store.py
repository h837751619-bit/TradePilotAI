from __future__ import annotations

import json
import re
from functools import cached_property
from typing import Callable
from urllib.error import HTTPError
from urllib.parse import quote
from urllib.request import Request, urlopen
from uuid import NAMESPACE_URL, uuid5

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Product
from .products import build_product_document


class ProductVectorStore:
    """Local embeddings and Qdrant product index; SQL remains the source of truth."""

    def __init__(self, ollama_url: str, qdrant_url: str, model: str, collection: str, timeout: float = 10.0, embedding_provider: str = "huggingface"):
        self.ollama_url = ollama_url.rstrip("/")
        self.qdrant_url = qdrant_url.rstrip("/")
        self.model = model
        self.embedding_provider = embedding_provider
        self.collection = f"{collection}_{embedding_provider}_{re.sub(r'[^a-z0-9_]', '_', model.lower())}"
        self.timeout = timeout

    @cached_property
    def local_model(self):
        from fastembed import TextEmbedding

        return TextEmbedding(model_name=self.model)

    def _json(self, url: str, payload: dict | None = None, method: str = "GET") -> dict:
        data = json.dumps(payload).encode() if payload is not None else None
        request = Request(url, data=data, method=method, headers={"Content-Type": "application/json"})
        with urlopen(request, timeout=self.timeout) as response:
            return json.loads(response.read().decode())

    def embed(self, text: str, *, is_query: bool = False) -> list[float]:
        if self.embedding_provider == "huggingface":
            prefix = ("query: " if is_query else "passage: ") if "e5" in self.model.lower() else ""
            return next(self.local_model.embed([prefix + text])).tolist()
        if self.embedding_provider != "ollama":
            raise ValueError(f"Unsupported embedding provider: {self.embedding_provider}")
        result = self._json(f"{self.ollama_url}/api/embed", {"model": self.model, "input": text}, "POST")
        vectors = result.get("embeddings") or []
        if not vectors or not vectors[0]:
            raise ValueError("Embedding model returned no vector")
        return vectors[0]

    def ensure_collection(self, dimensions: int) -> None:
        url = f"{self.qdrant_url}/collections/{quote(self.collection)}"
        try:
            info = self._json(url)
        except HTTPError as exc:
            if exc.code != 404:
                raise
            self._json(url, {"vectors": {"size": dimensions, "distance": "Cosine"}}, "PUT")
            return
        size = info["result"]["config"]["params"]["vectors"]["size"]
        if size != dimensions:
            raise ValueError("Vector dimensions changed; use a new collection or rebuild the index")

    def upsert_product(self, product: Product) -> None:
        if not product.is_active:
            self.delete_product(product.sku)
            return
        document = build_product_document(product)
        vector = self.embed(document.text)
        self.ensure_collection(len(vector))
        self._json(
            f"{self.qdrant_url}/collections/{quote(self.collection)}/points?wait=true",
            {"points": [{"id": str(uuid5(NAMESPACE_URL, product.sku)), "vector": vector,
                         "payload": {**document.metadata, "text": document.text}}]},
            "PUT",
        )

    def delete_product(self, sku: str) -> None:
        url = f"{self.qdrant_url}/collections/{quote(self.collection)}/points/delete?wait=true"
        try:
            self._json(url, {"points": [str(uuid5(NAMESPACE_URL, sku))]}, "POST")
        except HTTPError as exc:
            if exc.code != 404:
                raise

    def search(self, query: str, limit: int = 5, min_score: float = 0.45) -> dict[str, float]:
        vector = self.embed(query, is_query=True)
        url = f"{self.qdrant_url}/collections/{quote(self.collection)}/points/query"
        try:
            response = self._json(
                url,
                {"query": vector, "limit": limit, "score_threshold": min_score, "with_payload": True},
                "POST",
            )
        except HTTPError as exc:
            if exc.code == 404:
                return {}
            raise
        return {point["payload"]["sku"]: point["score"] for point in response["result"]["points"]}

    def rebuild(self, session: Session, progress_callback: Callable[[int, int], None] | None = None) -> int:
        products = session.scalars(select(Product).where(Product.is_active.is_(True))).all()
        total = len(products)
        if progress_callback:
            progress_callback(0, total)
        if not products:
            try:
                self._json(
                    f"{self.qdrant_url}/collections/{quote(self.collection)}", method="DELETE"
                )
            except HTTPError as exc:
                if exc.code != 404:
                    raise
            return 0
        for product in products:
            self.upsert_product(product)
            if progress_callback:
                progress_callback(products.index(product) + 1, total)
        active_ids = {str(uuid5(NAMESPACE_URL, product.sku)) for product in products}
        scroll_url = f"{self.qdrant_url}/collections/{quote(self.collection)}/points/scroll"
        offset = None
        while True:
            response = self._json(scroll_url, {"limit": 100, "offset": offset, "with_payload": False}, "POST")
            page = response["result"]
            stale = [point["id"] for point in page["points"] if str(point["id"]) not in active_ids]
            if stale:
                self._json(
                    f"{self.qdrant_url}/collections/{quote(self.collection)}/points/delete?wait=true",
                    {"points": stale}, "POST",
                )
            offset = page.get("next_page_offset")
            if offset is None:
                break
        return len(products)
