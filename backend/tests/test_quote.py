import pytest

from tradepilot.inventory import seed_inventory
from tradepilot.quote import generate_quote
from tradepilot.seed import seed_products


def test_quote_combines_product_price_and_inventory(session) -> None:
    seed_products(session)
    seed_inventory(session)
    quote = generate_quote(session, "NOVA-CHAIR-001", quantity=100, customer_name="Acme Hotels")
    assert quote.customer_name == "Acme Hotels"
    assert quote.sku == "NOVA-CHAIR-001"
    assert quote.quantity == 100
    assert quote.unit_price_usd == 40.38
    assert quote.total_price_usd == 4038.0
    assert quote.inventory_sufficient is True


def test_quote_rejects_insufficient_inventory(session) -> None:
    seed_products(session)
    seed_inventory(session)
    with pytest.raises(ValueError, match="Insufficient inventory"):
        generate_quote(session, "NOVA-SOFA-001", quantity=1000)
