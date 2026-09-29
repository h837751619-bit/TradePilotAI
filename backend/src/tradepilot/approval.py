from dataclasses import replace

from .quote import QuoteDraft


def approve_quote(quote: QuoteDraft) -> QuoteDraft:
    if quote.status != "draft":
        raise ValueError("Only draft quotes can be approved")
    return replace(quote, status="approved")
