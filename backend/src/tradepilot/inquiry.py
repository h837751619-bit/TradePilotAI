from __future__ import annotations

import re
from dataclasses import dataclass


@dataclass(frozen=True)
class InquiryRequirements:
    raw_text: str
    quantity: int | None
    destination_country: str | None
    project_type: str | None
    product_keywords: list[str]


PRODUCT_PHRASES = ("outdoor chair", "outdoor table", "outdoor sofa", "patio umbrella", "outdoor furniture")
MATERIALS = ("aluminum", "aluminium", "hpl", "olefin", "polyester")
COUNTRIES = ("Germany", "Italy", "France", "UK", "United Kingdom", "USA", "Australia")
PROJECT_TYPES = ("hotel", "restaurant", "resort", "cafe", "commercial")


def parse_inquiry(text: str) -> InquiryRequirements:
    normalized = " ".join(text.split())
    quantity_match = re.search(
        r"\b(\d[\d,]*)\s+(?:units?|pieces?|pcs?|sets?|[a-z]+(?:s)?)\b",
        normalized,
        re.IGNORECASE,
    )
    quantity = int(quantity_match.group(1).replace(",", "")) if quantity_match else None
    lower_text = normalized.lower()

    country = next((country for country in COUNTRIES if country.lower() in lower_text), None)
    project_type = next((project for project in PROJECT_TYPES if project in lower_text), None)
    keywords = [phrase for phrase in PRODUCT_PHRASES + MATERIALS if phrase in lower_text]
    return InquiryRequirements(normalized, quantity, country, project_type, keywords)
