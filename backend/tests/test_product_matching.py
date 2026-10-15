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
    assert candidates[0]["semantic_score"] is None
    assert candidates[0]["unit_price_usd"] > 0
    assert candidates[0]["lead_time_days"] > 0


def test_semantic_score_is_exposed_and_breaks_equal_score_ties(session) -> None:
    seed_products(session)
    seed_inventory(session)
    candidates = rank_product_candidates(
        session,
        [],
        20,
        None,
        semantic_matches={"NOVA-TABLE-001": 0.81, "NOVA-CHAIR-001": 0.80},
    )
    assert candidates[0]["sku"] == "NOVA-TABLE-001"
    assert candidates[0]["semantic_score"] == 0.81
