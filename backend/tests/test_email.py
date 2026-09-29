from tradepilot.email import generate_email_draft
from tradepilot.inquiry import parse_inquiry
from tradepilot.quote import QuoteDraft


def test_email_draft_contains_quote_details_and_is_not_sendable() -> None:
    inquiry = parse_inquiry("We need 120 aluminum outdoor chairs for a hotel project in Germany.")
    quote = QuoteDraft(
        customer_name="Acme Hotels",
        sku="NOVA-CHAIR-001",
        quantity=120,
        unit_price_usd=40.38,
        total_price_usd=4845.6,
        discount_percent=5,
        inventory_sufficient=True,
        status="draft",
    )
    draft = generate_email_draft(inquiry, quote)
    assert draft.status == "draft"
    assert "Acme Hotels" in draft.body
    assert "120" in draft.body
    assert "USD 40.38" in draft.body
    assert "Germany" in draft.body
    assert draft.sent is False
