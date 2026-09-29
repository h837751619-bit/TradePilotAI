from tradepilot.models import Product


def test_product_persists_all_business_fields(session) -> None:
    product = Product(
        sku="NOVA-CHAIR-001",
        name="Nova Aluminum Outdoor Chair",
        category="Outdoor Chair",
        description="Stackable chair for hotel and restaurant projects.",
        material="Aluminum",
        colors="Black,White",
        min_order_quantity=50,
        lead_time_days=35,
        unit_price_usd=42.5,
        is_active=True,
    )
    session.add(product)
    session.commit()
    saved = session.query(Product).one()
    assert saved.sku == "NOVA-CHAIR-001"
    assert saved.min_order_quantity == 50
    assert saved.unit_price_usd == 42.5
