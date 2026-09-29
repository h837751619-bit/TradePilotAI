from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    on_hand_quantity: Mapped[int] = mapped_column(Integer)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)


@dataclass(frozen=True)
class InventoryCheck:
    sku: str
    available_quantity: int
    requested_quantity: int
    sufficient: bool
    shortfall: int


INVENTORY_SEED = {
    "NOVA-CHAIR-001": 500,
    "NOVA-TABLE-001": 120,
    "NOVA-SOFA-001": 50,
    "NOVA-UMBRELLA-001": 200,
    "NOVA-SET-001": 80,
}


def seed_inventory(session: Session) -> None:
    existing = set(session.scalars(select(Inventory.sku)).all())
    for sku, quantity in INVENTORY_SEED.items():
        if sku not in existing:
            session.add(Inventory(sku=sku, on_hand_quantity=quantity, reserved_quantity=0))
    session.commit()


def check_inventory(session: Session, sku: str, requested_quantity: int) -> InventoryCheck:
    if requested_quantity < 0:
        raise ValueError("Requested quantity cannot be negative")
    record = session.scalar(select(Inventory).where(Inventory.sku == sku))
    if record is None:
        raise LookupError(f"Unknown product SKU: {sku}")
    available = record.on_hand_quantity - record.reserved_quantity
    shortfall = max(requested_quantity - available, 0)
    return InventoryCheck(sku, available, requested_quantity, shortfall == 0, shortfall)
