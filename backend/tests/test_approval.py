import pytest

from tradepilot.approval import approve_quote
from tradepilot.quote import QuoteDraft
from tradepilot.risk import assess_quote_risk


def draft(**overrides) -> QuoteDraft:
    values = {
        "customer_name": "Acme Hotels",
        "sku": "NOVA-CHAIR-001",
        "quantity": 100,
        "unit_price_usd": 40.38,
        "total_price_usd": 4038.0,
        "discount_percent": 5,
        "inventory_sufficient": True,
        "status": "draft",
    }
    values.update(overrides)
    return QuoteDraft(**values)


def test_discounted_quote_requires_human_approval() -> None:
    risk = assess_quote_risk(draft())
    assert risk.requires_approval is True
    assert "discount" in risk.reasons[0].lower()


def test_approval_changes_only_draft_status() -> None:
    approved = approve_quote(draft(discount_percent=0))
    assert approved.status == "approved"


def test_approval_rejects_non_draft_quote() -> None:
    with pytest.raises(ValueError, match="draft"):
        approve_quote(draft(status="approved"))
