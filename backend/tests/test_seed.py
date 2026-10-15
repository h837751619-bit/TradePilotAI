from sqlalchemy import select

from tradepilot.inventory import INVENTORY_SEED, Inventory, seed_inventory
from tradepilot.models import Product
from tradepilot.seed import PRODUCTS, seed_products


def test_seed_is_deterministic_and_idempotent(session) -> None:
    seed_products(session)
    seed_products(session)
    products = session.scalars(select(Product)).all()
    assert len(products) == len(PRODUCTS)
    assert len(products) >= 25
    assert {product.category for product in products} == {
        "Outdoor Chair", "Outdoor Table", "Outdoor Sofa", "Outdoor Umbrella", "Furniture Set"
    }


def test_inventory_seed_covers_all_catalog_products_without_overwriting(session) -> None:
    seed_products(session)
    seed_inventory(session)
    seed_inventory(session)
    inventory = {record.sku: record for record in session.scalars(select(Inventory)).all()}
    assert set(INVENTORY_SEED) <= set(inventory)
    assert len(inventory) == len(INVENTORY_SEED)
    assert all(record.on_hand_quantity == INVENTORY_SEED[record.sku] for record in inventory.values())
