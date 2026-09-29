from tradepilot.customer import lookup_customer, seed_customers


def test_customer_lookup_finds_existing_customer(session) -> None:
    seed_customers(session)
    customer = lookup_customer(session, "Acme Hotels")
    assert customer is not None
    assert customer.company_name == "Acme Hotels"
    assert customer.country == "Germany"


def test_customer_lookup_returns_none_for_new_customer(session) -> None:
    seed_customers(session)
    assert lookup_customer(session, "New Buyer Inc") is None
