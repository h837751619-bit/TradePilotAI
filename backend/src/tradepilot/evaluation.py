from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .db import Base
from .inquiry import parse_inquiry
from .inventory import Inventory, seed_inventory  # noqa: F401
from .models import Product  # noqa: F401
from .product_matching import rank_product_candidates
from .seed import seed_products
from .workflow import create_quote_from_inquiry


def evaluate_dataset(dataset_path: str | Path) -> dict[str, float | int]:
    dataset = Path(dataset_path)
    if not dataset.is_absolute() and not dataset.exists():
        # Resolve paths such as ../data/... relative to the backend directory,
        # so evaluation behaves consistently from the repository root or backend.
        backend_root = Path(__file__).resolve().parents[2]
        dataset = backend_root / dataset
    cases = json.loads(dataset.read_text())
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    parsed_correct = product_correct = quote_success = failure_detected = 0
    failure_reasons: dict[str, int] = {}
    with Session(engine) as session:
        seed_products(session)
        seed_inventory(session)
        for case in cases:
            try:
                result = create_quote_from_inquiry(session, case["text"])
            except (LookupError, ValueError) as exc:
                reason = "inventory" if "inventory" in str(exc).lower() else "quantity" if "quantity" in str(exc).lower() else "product"
                failure_reasons[reason] = failure_reasons.get(reason, 0) + 1
                failure_detected += int(reason == case.get("expected_error"))
                continue
            if case.get("expected_error"):
                continue
            parsed_correct += int(result.inquiry.quantity == case["quantity"] and result.inquiry.destination_country == case["country"])
            product_correct += int(result.quote.sku == case["product_sku"])
            quote_success += int(result.quote.inventory_sufficient)
    success_cases = sum(1 for case in cases if not case.get("expected_error")) or 1
    return {
        "cases": len(cases),
        "requirement_accuracy": parsed_correct / success_cases,
        "product_match_rate": product_correct / success_cases,
        "quote_success_rate": quote_success / success_cases,
        "task_success_rate": (parsed_correct + product_correct + quote_success) / (success_cases * 3),
        "failure_detection_rate": failure_detected / max(sum(1 for case in cases if case.get("expected_error")), 1),
        "failure_reasons": failure_reasons,
    }


def evaluate_rag_dataset(
    dataset_path: str | Path,
    semantic_retriever=None,
) -> dict[str, float | int | str | list[dict[str, object]]]:
    """Measure ranked product retrieval for paraphrased inquiries."""
    dataset = Path(dataset_path)
    if not dataset.is_absolute() and not dataset.exists():
        dataset = Path(__file__).resolve().parents[2] / dataset
    cases = json.loads(dataset.read_text())
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    top1_hits = top3_hits = evaluated = 0
    reciprocal_rank_sum = 0.0
    misses: list[dict[str, object]] = []
    with Session(engine) as session:
        seed_products(session)
        seed_inventory(session)
        for case in cases:
            inquiry = parse_inquiry(case["text"])
            semantic_matches = semantic_retriever(case["text"]) if semantic_retriever else None
            candidates = rank_product_candidates(
                session,
                inquiry.product_keywords,
                inquiry.quantity,
                inquiry.project_type,
                semantic_matches=semantic_matches,
            )
            skus = [candidate["sku"] for candidate in candidates]
            expected = case["product_sku"]
            evaluated += 1
            rank = skus.index(expected) + 1 if expected in skus else None
            top1_hits += int(rank == 1)
            top3_hits += int(rank is not None and rank <= 3)
            reciprocal_rank_sum += 1 / rank if rank is not None else 0
            if rank is None or rank > 3:
                misses.append({"text": case["text"], "expected_sku": expected, "returned_skus": skus[:3], "rank": rank})
    return {
        "mode": "semantic" if semantic_retriever else "rules",
        "cases": len(cases),
        "evaluated_cases": evaluated,
        "top1_recall": top1_hits / max(evaluated, 1),
        "top3_recall": top3_hits / max(evaluated, 1),
        "mrr": reciprocal_rank_sum / max(evaluated, 1),
        "misses": misses,
    }
