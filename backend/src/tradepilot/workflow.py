from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy.orm import Session

from .inquiry import InquiryRequirements, parse_inquiry
from .quote import QuoteDraft, generate_quote
from .rag.products import retrieve_product_documents


@dataclass(frozen=True)
class InquiryQuoteResult:
    inquiry: InquiryRequirements
    quote: QuoteDraft


def create_quote_from_inquiry(
    session: Session,
    inquiry_text: str,
    customer_name: str = "",
) -> InquiryQuoteResult:
    inquiry = parse_inquiry(inquiry_text)
    if inquiry.quantity is None:
        raise ValueError("Inquiry quantity is required")
    query = " ".join(inquiry.product_keywords)
    if not query:
        raise LookupError("No product keywords found")
    documents = retrieve_product_documents(session, query, limit=1)
    if not documents:
        raise LookupError("No matching product found")
    quote = generate_quote(session, documents[0].metadata["sku"], inquiry.quantity, customer_name)
    return InquiryQuoteResult(inquiry=inquiry, quote=quote)
