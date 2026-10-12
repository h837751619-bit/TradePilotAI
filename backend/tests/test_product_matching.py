from tradepilot.inventory import seed_inventory
from tradepilot.product_matching import rank_product_candidates
from tradepilot.seed import seed_products


def test_product_candidates_include_score_and_explanation(session) -> None:
    seed_products(session)
    seed_inventory(session)
    candidates = rank_product_candidates(session, ["aluminum", "outdoor chair"], 120, "hotel")
    assert candidates
    assert candidates[0]["sku"] == "NOVA-CHAIR-001"
    assert candidates[0]["score"] > 0
    assert candidates[0]["reasons"]
    assert candidates[0]["unmet_conditions"] == []
    assert candidates[0]["inventory_sufficient"] is True
    assert candidates[0]["unit_price_usd"] > 0
    assert candidates[0]["lead_time_days"] > 0
