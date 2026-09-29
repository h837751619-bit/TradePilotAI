from sqlalchemy import select
from sqlalchemy.orm import Session

from .models import Product

PRODUCTS = [
    Product(sku="NOVA-CHAIR-001", name="Nova Aluminum Outdoor Chair", category="Outdoor Chair", description="Stackable aluminum chair for hotel and restaurant projects.", material="Powder-coated aluminum", colors="Black,White,Khaki", min_order_quantity=50, lead_time_days=35, unit_price_usd=42.5, is_active=True),
    Product(sku="NOVA-TABLE-001", name="Nova Round Outdoor Table", category="Outdoor Table", description="Weather-resistant round table for hotel terraces and restaurants.", material="Aluminum and HPL", colors="Black,White", min_order_quantity=20, lead_time_days=40, unit_price_usd=128.0, is_active=True),
    Product(sku="NOVA-SOFA-001", name="Nova Modular Outdoor Sofa", category="Outdoor Sofa", description="Modular outdoor sofa designed for hospitality and hotel projects.", material="Aluminum and Olefin fabric", colors="Grey,Beige", min_order_quantity=10, lead_time_days=45, unit_price_usd=315.0, is_active=True),
    Product(sku="NOVA-UMBRELLA-001", name="Nova Commercial Patio Umbrella", category="Outdoor Umbrella", description="Commercial patio umbrella for restaurant and resort outdoor spaces.", material="Aluminum and solution-dyed polyester", colors="White,Red,Green", min_order_quantity=10, lead_time_days=30, unit_price_usd=168.0, is_active=True),
    Product(sku="NOVA-SET-001", name="Nova 5-Piece Furniture Set", category="Furniture Set", description="Outdoor dining set suitable for hotel balconies, cafes, and restaurants.", material="Aluminum and HPL", colors="Black,White", min_order_quantity=10, lead_time_days=45, unit_price_usd=480.0, is_active=True),
]


def seed_products(session: Session) -> None:
    existing = set(session.scalars(select(Product.sku)).all())
    for template in PRODUCTS:
        if template.sku not in existing:
            session.add(Product(**{column.name: getattr(template, column.name) for column in Product.__table__.columns if column.name != "id"}))
    session.commit()
