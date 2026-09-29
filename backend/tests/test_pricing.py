import pytest

from tradepilot.pricing import calculate_price
from tradepilot.seed import seed_products


def test_price_uses_base_price_below_discount_threshold(session) -> None:
    seed_products(session)
    result = calculate_price(session, "NOVA-CHAIR-001", quantity=50)
    assert result.unit_price_usd == 42.5
    assert result.total_price_usd == 2125.0
    assert result.discount_percent == 0


def test_price_applies_quantity_tier(session) -> None:
    seed_products(session)
    result = calculate_price(session, "NOVA-CHAIR-001", quantity=500)
    assert result.unit_price_usd == 38.25
    assert result.discount_percent == 10


def test_price_rejects_quantity_below_moq(session) -> None:
    seed_products(session)
    with pytest.raises(ValueError, match="MOQ"):
        calculate_price(session, "NOVA-CHAIR-001", quantity=10)


def test_price_rejects_unknown_sku(session) -> None:
    with pytest.raises(LookupError, match="Unknown product SKU"):
        calculate_price(session, "UNKNOWN", quantity=100)
