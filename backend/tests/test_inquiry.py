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


def test_parser_returns_none_for_missing_optional_fields() -> None:
    inquiry = parse_inquiry("Please send your outdoor furniture catalog.")
    assert inquiry.quantity is None
    assert inquiry.destination_country is None
    assert inquiry.project_type is None
