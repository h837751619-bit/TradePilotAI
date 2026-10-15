from __future__ import annotations

import json

from sqlalchemy import select
from sqlalchemy.orm import Session

from ..ai_provider import AIProvider, parse_json_object
from ..models import Product

EVIDENCE_FIELDS = {
    "name",
    "category",
    "description",
    "material",
    "colors",
    "match_tags",
    "min_order_quantity",
    "lead_time_days",
    "unit_price_usd",
}


def _verified_explanation(product: Product, fields: list[str]) -> str:
    facts = "; ".join(
        f"{field.replace('_', ' ')}: {getattr(product, field)}"
        for field in fields
    )
    return f"{product.name} matches based on {facts}."


def _product_context(product: Product) -> dict:
    return {"sku": product.sku, **{field: getattr(product, field) for field in EVIDENCE_FIELDS}}


def explain_product_candidates(
    session: Session,
    inquiry: str,
    candidates: list[dict],
    provider: AIProvider,
) -> tuple[dict[str, dict], str, str]:
    """Generate grounded explanations and replace model citations with database values."""
    candidate_skus = [candidate["sku"] for candidate in candidates]
    products = session.scalars(select(Product).where(Product.sku.in_(candidate_skus))).all()
    products_by_sku = {product.sku: product for product in products}
    contexts = [_product_context(products_by_sku[sku]) for sku in candidate_skus if sku in products_by_sku]
    prompt = (
        "You explain why catalog products match a sales inquiry. Use only facts in CANDIDATES. "
        "Do not invent product capabilities or modify numbers. Return JSON only with this shape: "
        '{"matches":[{"sku":"...","explanation":"one concise sentence in the inquiry language",'
        '"evidence_fields":["description","material"]}]}. '
        "Use 1-4 evidence_fields chosen only from: "
        + ", ".join(sorted(EVIDENCE_FIELDS))
        + ". Include every candidate exactly once.\nINQUIRY: "
        + inquiry
        + "\nCANDIDATES: "
        + json.dumps(contexts, ensure_ascii=False)
    )
    response = provider.complete(prompt)
    data = parse_json_object(response.text)
    raw_matches = data.get("matches")
    if not isinstance(raw_matches, list):
        raise TypeError("RAG explanation response must contain a matches list")

    explanations: dict[str, dict] = {}
    for item in raw_matches:
        if not isinstance(item, dict):
            continue
        sku = str(item.get("sku") or "")
        explanation = str(item.get("explanation") or "").strip()
        product = products_by_sku.get(sku)
        if product is None or not explanation:
            continue
        raw_fields = item.get("evidence_fields") or []
        fields = [str(field) for field in raw_fields if str(field) in EVIDENCE_FIELDS][:4]
        evidence = [
            {"field": field, "value": getattr(product, field)}
            for field in dict.fromkeys(fields)
        ]
        explanations[sku] = {
            "explanation": _verified_explanation(product, list(dict.fromkeys(fields))),
            "model_explanation": explanation,
            "evidence": evidence,
        }
    return explanations, response.provider, response.model


def attach_fallback_explanations(candidates: list[dict]) -> None:
    for candidate in candidates:
        candidate["explanation"] = "; ".join(candidate["reasons"]) or "Rule-based catalog match"
        candidate["model_explanation"] = None
        candidate["evidence"] = []


def attach_ai_explanations(candidates: list[dict], explanations: dict[str, dict]) -> None:
    for candidate in candidates:
        result = explanations.get(candidate["sku"])
        if result:
            candidate.update(result)
        else:
            candidate["explanation"] = "; ".join(candidate["reasons"]) or "Rule-based catalog match"
            candidate["model_explanation"] = None
            candidate["evidence"] = []
