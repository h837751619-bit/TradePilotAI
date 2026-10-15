from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Optional

from sqlalchemy import DateTime, Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base
from .models import QuoteRecord


class Inventory(Base):
    __tablename__ = "inventory"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), unique=True, index=True)
    on_hand_quantity: Mapped[int] = mapped_column(Integer)
    reserved_quantity: Mapped[int] = mapped_column(Integer, default=0)


class InventoryMovement(Base):
    __tablename__ = "inventory_movements"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    quote_id: Mapped[Optional[int]] = mapped_column(Integer, index=True, nullable=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    quantity: Mapped[int] = mapped_column(Integer)
    movement_type: Mapped[str] = mapped_column(String(32), index=True)
    actor: Mapped[str] = mapped_column(String(120), default="system")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


class InventoryAdjustment(Base):
    __tablename__ = "inventory_adjustments"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    sku: Mapped[str] = mapped_column(String(64), index=True)
    previous_quantity: Mapped[int] = mapped_column(Integer)
    new_quantity: Mapped[int] = mapped_column(Integer)
    reason: Mapped[str] = mapped_column(String(300), default="manual adjustment")
    actor: Mapped[str] = mapped_column(String(120), default="manual")
    created_at: Mapped[datetime] = mapped_column(DateTime, default=datetime.utcnow)


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
    "NOVA-CHAIR-002": 180,
    "NOVA-CHAIR-003": 240,
    "NOVA-CHAIR-004": 95,
    "NOVA-CHAIR-005": 72,
    "NOVA-CHAIR-006": 160,
    "NOVA-TABLE-002": 90,
    "NOVA-TABLE-003": 36,
    "NOVA-TABLE-004": 140,
    "NOVA-TABLE-005": 64,
    "NOVA-TABLE-006": 48,
    "NOVA-SOFA-002": 42,
    "NOVA-SOFA-003": 24,
    "NOVA-SOFA-004": 12,
    "NOVA-SOFA-005": 55,
    "NOVA-UMBRELLA-002": 30,
    "NOVA-UMBRELLA-003": 110,
    "NOVA-UMBRELLA-004": 8,
    "NOVA-UMBRELLA-005": 75,
    "NOVA-SET-002": 18,
    "NOVA-SET-003": 40,
    "NOVA-SET-004": 7,
    "NOVA-SET-005": 14,
    "NOVA-SET-006": 22,
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


def reserve_inventory(session: Session, quote_id: int, sku: str, quantity: int, actor: str = "system") -> None:
    # Serialize all inventory transitions for a quote before checking movement
    # idempotency. On MySQL this row lock also prevents concurrent duplicate reserves.
    quote = session.scalar(select(QuoteRecord).where(QuoteRecord.id == quote_id).with_for_update())
    if quote is None:
        raise LookupError("Quote not found")
    existing = session.scalar(select(InventoryMovement).where(InventoryMovement.quote_id == quote_id, InventoryMovement.movement_type == "reserve"))
    if existing is not None:
        return
    record = session.scalar(select(Inventory).where(Inventory.sku == sku).with_for_update())
    if record is None:
        raise LookupError(f"Unknown product SKU: {sku}")
    available = record.on_hand_quantity - record.reserved_quantity
    if available < quantity:
        raise ValueError(f"Insufficient inventory: shortfall {quantity - available}")
    record.reserved_quantity += quantity
    session.add(InventoryMovement(quote_id=quote_id, sku=sku, quantity=quantity, movement_type="reserve", actor=actor))


def deduct_reserved_inventory(session: Session, quote_id: int, actor: str = "system") -> None:
    quote = session.scalar(select(QuoteRecord).where(QuoteRecord.id == quote_id).with_for_update())
    if quote is None:
        raise LookupError("Quote not found")
    reservation = session.scalar(select(InventoryMovement).where(InventoryMovement.quote_id == quote_id, InventoryMovement.movement_type == "reserve"))
    if reservation is None:
        raise LookupError("No inventory reservation found for quote")
    existing = session.scalar(select(InventoryMovement).where(InventoryMovement.quote_id == quote_id, InventoryMovement.movement_type == "deduct"))
    if existing is not None:
        return
    record = session.scalar(select(Inventory).where(Inventory.sku == reservation.sku).with_for_update())
    if record is None or record.on_hand_quantity < reservation.quantity or record.reserved_quantity < reservation.quantity:
        raise ValueError("Inventory reservation is no longer valid")
    record.on_hand_quantity -= reservation.quantity
    record.reserved_quantity -= reservation.quantity
    session.add(InventoryMovement(quote_id=quote_id, sku=reservation.sku, quantity=reservation.quantity, movement_type="deduct", actor=actor))


def release_reserved_inventory(session: Session, quote_id: int, actor: str = "system") -> None:
    quote = session.scalar(select(QuoteRecord).where(QuoteRecord.id == quote_id).with_for_update())
    if quote is None:
        raise LookupError("Quote not found")
    reservation = session.scalar(select(InventoryMovement).where(InventoryMovement.quote_id == quote_id, InventoryMovement.movement_type == "reserve"))
    if reservation is None:
        return
    existing = session.scalar(select(InventoryMovement).where(InventoryMovement.quote_id == quote_id, InventoryMovement.movement_type == "release"))
    if existing is not None:
        return
    record = session.scalar(select(Inventory).where(Inventory.sku == reservation.sku).with_for_update())
    if record is None or record.reserved_quantity < reservation.quantity:
        raise ValueError("Inventory reservation is no longer valid")
    record.reserved_quantity -= reservation.quantity
    session.add(InventoryMovement(quote_id=quote_id, sku=reservation.sku, quantity=reservation.quantity, movement_type="release", actor=actor))
