import pytest

from tradepilot.inventory import check_inventory, seed_inventory


def test_inventory_seed_is_idempotent_and_reports_available_quantity(session) -> None:
    seed_inventory(session)
    seed_inventory(session)
    result = check_inventory(session, "NOVA-CHAIR-001", requested_quantity=100)
    assert result.sku == "NOVA-CHAIR-001"
    assert result.available_quantity == 500
    assert result.sufficient is True


def test_inventory_reports_insufficient_quantity(session) -> None:
    seed_inventory(session)
    result = check_inventory(session, "NOVA-SOFA-001", requested_quantity=1000)
    assert result.sufficient is False
    assert result.shortfall == 950


def test_inventory_rejects_unknown_sku(session) -> None:
    seed_inventory(session)
    with pytest.raises(LookupError, match="Unknown product SKU"):
        check_inventory(session, "UNKNOWN", requested_quantity=1)
