from __future__ import annotations

from dataclasses import dataclass

from .inquiry import InquiryRequirements
from .quote import QuoteDraft


@dataclass(frozen=True)
class EmailDraft:
    subject: str
    body: str
    status: str
    sent: bool = False


def generate_email_draft(inquiry: InquiryRequirements, quote: QuoteDraft) -> EmailDraft:
    recipient = quote.customer_name or "there"
    destination = inquiry.destination_country or "your market"
    subject = f"Quotation for {quote.quantity} units of {quote.sku}"
    body = (
        f"Dear {recipient},\n\n"
        f"Thank you for your inquiry regarding outdoor furniture for {destination}. "
        f"We are pleased to share the following quotation:\n\n"
        f"- Product: {quote.sku}\n"
        f"- Quantity: {quote.quantity}\n"
        f"- Unit price: USD {quote.unit_price_usd:.2f}\n"
        f"- Total: USD {quote.total_price_usd:.2f}\n\n"
        "Please note that this quotation is subject to final confirmation of specifications, "
        "shipping terms, and delivery schedule.\n\n"
        "Best regards,\nNova Outdoor Sales Team"
    )
    return EmailDraft(subject=subject, body=body, status="draft")
