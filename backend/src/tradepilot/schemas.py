from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, ConfigDict, Field


class ProductResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    sku: str
    name: str
    category: str
    description: str
    material: str
    colors: str
    match_tags: str
    min_order_quantity: int
    lead_time_days: int
    unit_price_usd: float
    is_active: bool
    on_hand_quantity: int = 0
    reserved_quantity: int = 0
    available_quantity: int = 0


class ProductQuery(BaseModel):
    q: Optional[str] = None
    category: Optional[str] = None
    limit: int = Field(default=20, ge=1, le=100)
