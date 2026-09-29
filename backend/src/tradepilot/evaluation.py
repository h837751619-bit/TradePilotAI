from __future__ import annotations

import json
from pathlib import Path

from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from .db import Base
from .inventory import Inventory, seed_inventory  # noqa: F401
from .models import Product  # noqa: F401
from .seed import seed_products
from .workflow import create_quote_from_inquiry


def evaluate_dataset(dataset_path: str | Path) -> dict[str, float | int]:
    cases = json.loads(Path(dataset_path).read_text())
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
