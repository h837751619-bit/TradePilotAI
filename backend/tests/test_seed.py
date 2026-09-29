from sqlalchemy import select

from tradepilot.models import Product
from tradepilot.seed import seed_products


def test_seed_is_deterministic_and_idempotent(session) -> None:
    seed_products(session)
    seed_products(session)
    products = session.scalars(select(Product)).all()
    assert len(products) == 5
    assert {product.category for product in products} == {
        "Outdoor Chair", "Outdoor Table", "Outdoor Sofa", "Outdoor Umbrella", "Furniture Set"
    }
