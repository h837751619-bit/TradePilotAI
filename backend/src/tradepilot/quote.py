from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .inventory import check_inventory
from .pricing import calculate_price


@dataclass(frozen=True)
class QuoteDraft:
    customer_name: str
    sku: str
    quantity: int
    unit_price_usd: float
    total_price_usd: float
    discount_percent: int
    inventory_sufficient: bool
    status: str


def generate_quote(
    session: Session,
    sku: str,
    quantity: int,
    customer_name: str = "",
) -> QuoteDraft:
    inventory = check_inventory(session, sku, quantity)
    if not inventory.sufficient:
        raise ValueError(f"Insufficient inventory: shortfall {inventory.shortfall}")
    price = calculate_price(session, sku, quantity)
    return QuoteDraft(
        customer_name=customer_name,
        sku=sku,
        quantity=quantity,
        unit_price_usd=price.unit_price_usd,
        total_price_usd=price.total_price_usd,
        discount_percent=price.discount_percent,
        inventory_sufficient=inventory.sufficient,
        status="draft",
    )
