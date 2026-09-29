from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Product


@dataclass(frozen=True)
class PriceCalculation:
    sku: str
    quantity: int
    base_unit_price_usd: float
    unit_price_usd: float
    discount_percent: int
    total_price_usd: float


def calculate_price(session: Session, sku: str, quantity: int) -> PriceCalculation:
    if quantity <= 0:
        raise ValueError("Quantity must be positive")
    product = session.scalar(select(Product).where(Product.sku == sku, Product.is_active.is_(True)))
    if product is None:
        raise LookupError(f"Unknown product SKU: {sku}")
    if quantity < product.min_order_quantity:
        raise ValueError(f"Quantity is below MOQ ({product.min_order_quantity})")

    discount_percent = 10 if quantity >= 500 else 5 if quantity >= 100 else 0
    unit_price = round(product.unit_price_usd * (1 - discount_percent / 100), 2)
    return PriceCalculation(
        sku=sku,
        quantity=quantity,
        base_unit_price_usd=product.unit_price_usd,
        unit_price_usd=unit_price,
        discount_percent=discount_percent,
        total_price_usd=round(unit_price * quantity, 2),
    )
