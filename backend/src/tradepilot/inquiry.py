from __future__ import annotations

import re
from dataclasses import dataclass

from .ai_provider import AIProvider, parse_json_object


@dataclass(frozen=True)
class InquiryRequirements:
    raw_text: str
    quantity: int | None
    destination_country: str | None
    project_type: str | None
    product_keywords: list[str]
    budget_usd: float | None = None
    max_lead_time_days: int | None = None
    ai_provider: str = "rules"


PRODUCT_PHRASES = (
    "outdoor chair",
    "outdoor table",
    "outdoor sofa",
    "patio umbrella",
    "outdoor furniture",
    "chairs",
    "chair",
    "tables",
    "table",
    "sofas",
    "sofa",
    "umbrellas",
    "umbrella",
)
MATERIALS = ("aluminum", "aluminium", "hpl", "olefin", "polyester")
COUNTRIES = (
    "Germany", "Italy", "France", "UK", "United Kingdom", "USA", "United States",
    "Australia", "China", "Norway", "Sweden", "Denmark", "Finland", "Iceland",
    "Netherlands", "Belgium", "Luxembourg", "Spain", "Portugal", "Switzerland",
    "Austria", "Poland", "Czech Republic", "Ireland", "Canada", "New Zealand",
    "Japan", "South Korea", "Singapore", "India", "Vietnam", "Thailand", "Malaysia",
    "Indonesia", "Philippines", "United Arab Emirates", "Saudi Arabia", "South Africa",
    "Brazil", "Mexico", "Chile", "Argentina", "Turkey", "Israel",
)
PROJECT_TYPES = ("hotel", "restaurant", "resort", "cafe", "commercial")

INQUIRY_ALIASES = (
    ("weatherproof seating", "outdoor chair"),
    ("weather-resistant dining surfaces", "outdoor table"),
    ("dining surfaces", "outdoor table"),
    ("round dining surfaces", "outdoor table"),
    ("lounge units", "outdoor sofa"),
    ("modular hospitality lounge", "outdoor sofa"),
    ("outdoor seating", "outdoor chair"),
    ("patio seating", "outdoor chair"),
    ("commercial seating", "outdoor chair"),
    ("stackable outdoor seats", "outdoor chair"),
    ("outdoor seats", "outdoor chair"),
    ("metal seats", "outdoor chair"),
    ("户外椅", "outdoor chair"),
    ("户外座椅", "outdoor chair"),
    ("dining set", "furniture set"),
    ("balcony set", "furniture set"),
    ("furniture package", "furniture set"),
    ("couch", "outdoor sofa"),
    ("parasol", "patio umbrella"),
    ("sedute", "outdoor chair"),
    ("sedia", "outdoor chair"),
    ("sedie", "outdoor chair"),
    ("tavoli", "outdoor table"),
    ("tavolo", "outdoor table"),
    ("sofá", "outdoor sofa"),
    ("sofa", "outdoor sofa"),
    ("divani", "outdoor sofa"),
    ("座椅", "outdoor chair"),
    ("椅子", "outdoor chair"),
    ("桌子", "outdoor table"),
    ("餐桌", "outdoor table"),
    ("沙发", "outdoor sofa"),
    ("家具组合", "furniture set"),
    ("雨伞", "patio umbrella"),
)


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
    for alias, canonical in INQUIRY_ALIASES:
        if alias in lower_text and canonical not in keywords:
            keywords.append(canonical)
    budget_match = re.search(r"(?:budget|under|less than|up to)\s*[:=]?\s*\$?\s*([\d,]+(?:\.\d+)?)", lower_text)
    lead_match = re.search(r"(?:within|no later than|in)\s+(\d+)\s+days?", lower_text)
    budget = float(budget_match.group(1).replace(",", "")) if budget_match else None
    max_lead = int(lead_match.group(1)) if lead_match else None
    return InquiryRequirements(normalized, quantity, country, project_type, keywords, budget, max_lead)


def parse_inquiry_with_provider(text: str, provider: AIProvider | None = None) -> InquiryRequirements:
    fallback = parse_inquiry(text)
    if provider is None:
        return fallback
    prompt = (
        "Extract inquiry requirements as JSON with keys quantity, destination_country, "
        "project_type, product_keywords, budget_usd, max_lead_time_days. Return JSON only. Inquiry: " + text
    )
    try:
        result = provider.complete(prompt)
        data = parse_json_object(result.text)
        raw_keywords = data.get("product_keywords") or []
        if isinstance(raw_keywords, str):
            raw_keywords = [raw_keywords]
        ai_keywords = [str(keyword).lower().strip() for keyword in raw_keywords if str(keyword).strip()]
        merged_keywords = list(dict.fromkeys(fallback.product_keywords + ai_keywords))
        raw_project = str(data.get("project_type") or "").lower()
        normalized_project = next((project for project in PROJECT_TYPES if project in raw_project), fallback.project_type)
        return InquiryRequirements(
            raw_text=fallback.raw_text,
            quantity=data.get("quantity") or fallback.quantity,
            destination_country=data.get("destination_country") or fallback.destination_country,
            project_type=normalized_project,
            product_keywords=merged_keywords,
            budget_usd=data.get("budget_usd") or fallback.budget_usd,
            max_lead_time_days=data.get("max_lead_time_days") or fallback.max_lead_time_days,
            ai_provider=result.provider,
        )
    except (OSError, TimeoutError, ValueError, TypeError):
        return fallback
