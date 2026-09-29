import pytest

from tradepilot.inventory import seed_inventory
from tradepilot.seed import seed_products
from tradepilot.workflow import create_quote_from_inquiry


def test_inquiry_to_quote_workflow() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from tradepilot.db import Base
    from tradepilot.inventory import Inventory  # noqa: F401
    from tradepilot.models import Product  # noqa: F401

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session:
        seed_products(session)
        seed_inventory(session)
        result = create_quote_from_inquiry(
            session,
            "We need 120 aluminum outdoor chairs for a hotel project in Germany.",
            customer_name="Acme Hotels",
        )

    assert result.inquiry.quantity == 120
    assert result.quote.sku == "NOVA-CHAIR-001"
    assert result.quote.inventory_sufficient is True


def test_workflow_requires_extractable_quantity() -> None:
    from sqlalchemy import create_engine
    from sqlalchemy.orm import Session

    from tradepilot.db import Base

    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as session, pytest.raises(ValueError, match="quantity"):
        create_quote_from_inquiry(session, "Please send your outdoor furniture catalog.")
