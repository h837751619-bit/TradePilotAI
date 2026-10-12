from __future__ import annotations

from dataclasses import dataclass

from sqlalchemy import select
from sqlalchemy.orm import Session

from .ai_provider import AIProvider
from .inquiry import InquiryRequirements, parse_inquiry_with_provider
from .models import Product
from .product_matching import rank_product_candidates
from .quote import QuoteDraft, generate_quote


@dataclass(frozen=True)
class InquiryQuoteResult:
    inquiry: InquiryRequirements
    quote: QuoteDraft


def create_quote_from_inquiry(
    session: Session,
    inquiry_text: str,
    customer_name: str = "",
    ai_provider: AIProvider | None = None,
    selected_sku: str | None = None,
) -> InquiryQuoteResult:
    inquiry = parse_inquiry_with_provider(inquiry_text, ai_provider)
    if inquiry.quantity is None:
        raise ValueError("Inquiry quantity is required")
    if selected_sku:
        product = session.scalar(select(Product).where(Product.sku == selected_sku, Product.is_active.is_(True)))
        if product is None:
            raise LookupError("Selected product not found")
        sku = product.sku
    else:
        if not inquiry.product_keywords:
            raise LookupError("No product keywords found")
        candidates = rank_product_candidates(
            session,
            inquiry.product_keywords,
            inquiry.quantity,
            inquiry.project_type,
            budget_usd=inquiry.budget_usd,
            max_lead_time_days=inquiry.max_lead_time_days,
        )
        matching = [candidate for candidate in candidates if candidate["reasons"]]
        if not matching:
            raise LookupError("No matching product found")
        eligible = [candidate for candidate in matching if not candidate["unmet_conditions"]]
        if inquiry.budget_usd is not None or inquiry.max_lead_time_days is not None:
            if not eligible:
                raise LookupError("No product meets the requested budget, lead time, or inventory")
            sku = eligible[0]["sku"]
        else:
            sku = matching[0]["sku"]
    quote = generate_quote(session, sku, inquiry.quantity, customer_name)
    return InquiryQuoteResult(inquiry=inquiry, quote=quote)
