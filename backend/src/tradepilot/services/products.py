from __future__ import annotations

from typing import Optional

from sqlalchemy import or_, select
from sqlalchemy.orm import Session

from ..models import Product


def search_products(session: Session, q: Optional[str] = None, category: Optional[str] = None, limit: int = 20) -> list[Product]:
    statement = select(Product).where(Product.is_active.is_(True))
    if q:
        pattern = f"%{q.lower()}%"
        statement = statement.where(or_(
            Product.sku.ilike(pattern), Product.name.ilike(pattern),
            Product.category.ilike(pattern), Product.description.ilike(pattern),
        ))
    if category:
        statement = statement.where(Product.category == category)
    return list(session.scalars(statement.order_by(Product.id).limit(limit)).all())
