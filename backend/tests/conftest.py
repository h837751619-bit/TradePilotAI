import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import Session

from tradepilot.customer import Customer  # noqa: F401
from tradepilot.db import Base
from tradepilot.inventory import Inventory  # noqa: F401


@pytest.fixture
def session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    with Session(engine) as db:
        yield db
