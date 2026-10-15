from tradepilot.inquiry import parse_inquiry


def test_parser_extracts_core_export_inquiry_fields() -> None:
    inquiry = parse_inquiry(
        "We need 120 aluminum outdoor chairs for a hotel project in Germany. "
        "Please share colors and lead time."
    )
    assert inquiry.quantity == 120
    assert inquiry.destination_country == "Germany"
    assert inquiry.project_type == "hotel"
    assert "aluminum" in inquiry.product_keywords
    assert "outdoor chair" in inquiry.product_keywords

    constrained = parse_inquiry("Need 80 chairs with a budget under $45 within 30 days.")
    assert constrained.budget_usd == 45
    assert constrained.max_lead_time_days == 30


def test_parser_returns_none_for_missing_optional_fields() -> None:
    inquiry = parse_inquiry("Please send your outdoor furniture catalog.")
    assert inquiry.quantity is None
    assert inquiry.destination_country is None
    assert inquiry.project_type is None


def test_parser_recognizes_additional_export_destinations() -> None:
    norway = parse_inquiry("We need 50 chairs for a hotel project in Norway.")
    australia = parse_inquiry("We need 50 chairs for a hotel project in Australia.")

    assert norway.destination_country == "Norway"
    assert australia.destination_country == "Australia"


def test_parser_normalizes_multilingual_and_domain_synonyms() -> None:
    chinese = parse_inquiry("中国酒店需要 50 把耐候户外座椅。")
    italian = parse_inquiry("Servono 20 tavoli rotondi per un ristorante.")
    assert "outdoor chair" in chinese.product_keywords
    assert "outdoor table" in italian.product_keywords
