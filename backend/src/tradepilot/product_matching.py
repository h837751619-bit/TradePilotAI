from __future__ import annotations

from sqlalchemy import select
from sqlalchemy.orm import Session

from .inventory import Inventory
from .models import Product
from .rag.products import build_product_document


def rank_product_candidates(session: Session, keywords: list[str], quantity: int | None, project_type: str | None, budget_usd: float | None = None, max_lead_time_days: int | None = None, limit: int = 5, keyword_weight: int = 20, project_weight: int = 15, quantity_weight: int = 15, semantic_matches: dict[str, float] | None = None) -> list[dict]:
    products = session.scalars(select(Product).where(Product.is_active.is_(True))).all()
    inventory_by_sku = {item.sku: item for item in session.scalars(select(Inventory)).all()}
    normalized = {keyword.lower().rstrip("s").strip() for keyword in keywords}
    candidates = []
    for product in products:
        # Use the same normalized product document as Qdrant so rule and semantic
        # ranking see the same domain synonyms and use-case vocabulary.
        haystack = build_product_document(product).text.lower()
        matched = sorted({keyword for keyword in normalized if keyword and keyword in haystack})
        reasons = [f"Matches {keyword}" for keyword in matched]
        score = min(60, len(matched) * keyword_weight)
        similarity = (semantic_matches or {}).get(product.sku)
        if semantic_matches and not matched and similarity is None:
            continue
        if similarity is not None:
            score += round(40 * max(0.0, min(1.0, similarity)))
            reasons.append(f"Semantic match {similarity:.2f}")
        if project_type and project_type.lower() in haystack:
            score += project_weight
            reasons.append(f"Suitable for {project_type} projects")
        # Prefer the catalog category that directly matches the requested
        # product type.  Product descriptions can mention companion items
        # (e.g. a sofa set mentions a table), so raw text overlap alone can
        # otherwise rank a furniture set above a standalone table or sofa.
        category_terms = {
            "Outdoor Chair": ("chair", "seat", "seating"),
            "Outdoor Table": ("table", "tables"),
            "Outdoor Sofa": ("sofa", "sofas", "couch", "lounge"),
            "Outdoor Umbrella": ("umbrella", "umbrellas", "parasol", "shade"),
            "Furniture Set": ("set", "package", "combination"),
        }
        requested_category = next(
            (category for category, terms in category_terms.items() if any(term in " ".join(normalized) for term in terms)),
            None,
        )
        if requested_category and product.category == requested_category:
            score += 8
            reasons.append(f"Category matches {requested_category}")
        unmet: list[str] = []
        if quantity is not None and quantity < product.min_order_quantity:
            unmet.append(f"Quantity below MOQ ({product.min_order_quantity})")
        else:
            score += quantity_weight
        inventory = inventory_by_sku.get(product.sku)
        available = (inventory.on_hand_quantity - inventory.reserved_quantity) if inventory else 0
        inventory_sufficient = quantity is None or available >= quantity
        if not inventory_sufficient:
            unmet.append(f"Insufficient inventory (available {available})")
        if budget_usd is not None and product.unit_price_usd > budget_usd:
            unmet.append(f"Unit price above budget ({budget_usd:.2f})")
        elif budget_usd is not None:
            score += 10
        if max_lead_time_days is not None and product.lead_time_days > max_lead_time_days:
            unmet.append(f"Lead time exceeds {max_lead_time_days} days")
        elif max_lead_time_days is not None:
            score += 10
        candidates.append({"sku": product.sku, "name": product.name, "score": min(score, 100), "semantic_score": similarity, "reasons": reasons, "unmet_conditions": unmet, "inventory_available": available, "inventory_sufficient": inventory_sufficient, "unit_price_usd": product.unit_price_usd, "lead_time_days": product.lead_time_days})
    candidates.sort(key=lambda candidate: (-candidate["inventory_sufficient"], -candidate["score"], -(candidate["semantic_score"] or 0), candidate["sku"]))
    return candidates[:limit]
