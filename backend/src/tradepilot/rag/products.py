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


def _search_synonyms(product: Product) -> list[str]:
    """Add stable domain vocabulary without requiring an LLM for every product."""
    haystack = f"{product.name} {product.category} {product.description} {product.match_tags}".lower()
    synonyms: list[str] = []
    groups = (
        (("chair", "seat", "seating"), "outdoor seating, patio chair, hotel chair, commercial seating, weatherproof seating, garden chair"),
        (("table", "dining surface"), "outdoor dining table, patio table, terrace table, restaurant table, dining surface"),
        (("sofa", "couch", "lounge"), "outdoor sofa, modular lounge seating, hospitality lounge, patio couch"),
        (("umbrella", "parasol", "shade"), "commercial patio umbrella, outdoor shade, terrace parasol"),
        (("set", "dining set"), "outdoor furniture set, patio set, balcony dining set, hospitality furniture package"),
    )
    for needles, value in groups:
        if any(needle in haystack for needle in needles):
            synonyms.append(value)
    if any(term in haystack for term in ("aluminum", "aluminium", "metal")):
        synonyms.append("aluminum aluminium metal outdoor furniture")
    if any(term in haystack for term in ("hotel", "hospitality", "restaurant", "resort", "commercial")):
        synonyms.append("hotel restaurant resort cafe hospitality commercial project")
    return synonyms


def build_product_document(product: Product) -> ProductDocument:
    synonyms = ", ".join(_search_synonyms(product))
    text = (
        f"Product name: {product.name}. SKU: {product.sku}. Category: {product.category}. "
        f"Description: {product.description} Material: {product.material}. "
        f"Colors: {product.colors}. Search tags: {product.match_tags}. "
        f"Search synonyms and use cases: {synonyms}. "
        f"MOQ: {product.min_order_quantity}. "
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
