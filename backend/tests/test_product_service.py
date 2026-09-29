from tradepilot.seed import seed_products
from tradepilot.services.products import search_products


def test_search_is_case_insensitive_and_matches_description(session) -> None:
    seed_products(session)
    results = search_products(session, q="HOTEL", limit=10)
    assert results
    assert all("hotel" in f"{item.name} {item.description}".lower() for item in results)


def test_search_filters_category_and_limits_results(session) -> None:
    seed_products(session)
    results = search_products(session, category="Outdoor Chair", limit=1)
    assert len(results) == 1
    assert results[0].category == "Outdoor Chair"
