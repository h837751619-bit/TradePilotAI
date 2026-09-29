from __future__ import annotations

from dataclasses import dataclass

from .quote import QuoteDraft


@dataclass(frozen=True)
class QuoteRiskAssessment:
    requires_approval: bool
    reasons: list[str]


def assess_quote_risk(quote: QuoteDraft) -> QuoteRiskAssessment:
    reasons: list[str] = []
    if not quote.customer_name.strip():
        reasons.append("Customer name is missing")
    if quote.quantity >= 500:
        reasons.append("Large order requires approval")
    if quote.discount_percent > 0:
        reasons.append("Discounted quote requires approval")
    return QuoteRiskAssessment(requires_approval=bool(reasons), reasons=reasons)
