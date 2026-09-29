from __future__ import annotations

from sqlalchemy import Integer, String, select
from sqlalchemy.orm import Mapped, Session, mapped_column

from .db import Base


class Customer(Base):
    __tablename__ = "customers"

    id: Mapped[int] = mapped_column(Integer, primary_key=True)
    company_name: Mapped[str] = mapped_column(String(200), unique=True, index=True)
    contact_name: Mapped[str] = mapped_column(String(120), default="")
    country: Mapped[str] = mapped_column(String(80), default="")
    email: Mapped[str] = mapped_column(String(200), default="")


CUSTOMER_SEED = [
    {"company_name": "Acme Hotels", "contact_name": "Emma Rossi", "country": "Germany", "email": "emma@acme-hotels.example"},
    {"company_name": "Nordic Terrace Group", "contact_name": "Lars Jensen", "country": "Italy", "email": "lars@nordic-terrace.example"},
]


def seed_customers(session: Session) -> None:
    existing = set(session.scalars(select(Customer.company_name)).all())
    for values in CUSTOMER_SEED:
        if values["company_name"] not in existing:
            session.add(Customer(**values))
    session.commit()


def lookup_customer(session: Session, company_name: str) -> Customer | None:
    return session.scalar(select(Customer).where(Customer.company_name.ilike(company_name.strip())))


def search_customers(session: Session, query: str | None = None) -> list[Customer]:
    statement = select(Customer).order_by(Customer.id)
    if query:
        statement = statement.where(Customer.company_name.ilike(f"%{query}%"))
    return list(session.scalars(statement).all())
