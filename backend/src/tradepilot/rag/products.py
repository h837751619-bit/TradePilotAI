from __future__ import annotations

import re
from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..models import Product


@dataclass(frozen=True)
class ProductDocument:
    text: str
    metadata: dict[str, str | int | float]


def build_product_document(product: Product) -> ProductDocument:
    text = (
        f"{product.name}. SKU: {product.sku}. Category: {product.category}. "
        f"Description: {product.description} Material: {product.material}. "
        f"Colors: {product.colors}. MOQ: {product.min_order_quantity}. "
        f"Lead time: {product.lead_time_days} days. Base price: USD {product.unit_price_usd:.2f}."
    )
    return ProductDocument(
        text=text,
        metadata={"sku": product.sku, "category": product.category, "product_id": product.id},
    )


def retrieve_product_documents(session: Session, query: str, limit: int = 5) -> list[ProductDocument]:
    products = session.scalars(select(Product).where(Product.is_active.is_(True))).all()
    terms = {term for term in re.findall(r"[a-z0-9]+", query.lower()) if len(term) > 2}
    ranked = []
    for product in products:
        document = build_product_document(product)
        haystack = document.text.lower()
        score = sum(haystack.count(term) for term in terms)
        if score:
            ranked.append((score, product.id, document))
    ranked.sort(key=lambda item: (-item[0], item[1]))
    return [document for _, _, document in ranked[:limit]]
