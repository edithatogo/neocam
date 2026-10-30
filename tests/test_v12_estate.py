"""Economic retention and purchases must describe the same mixed equipment estate."""

from pathlib import Path
from typing import TYPE_CHECKING, cast

import numpy as np
import pytest

from scripts import analyse_v7
from src import equipment
from src.configuration import load_configuration
from src.equipment import OwnedAsset
from src.pathways_v6 import PathwaySpec
from src.portfolios_v7 import portfolio
from src.statewide import Parameters

if TYPE_CHECKING:
    from collections.abc import Callable

ROOT = Path(__file__).resolve().parents[1]

# src/script signatures declare bare containers; these restate the asserted shapes.
compare_regional = cast("Callable[..., dict[str, dict[str, np.ndarray]]]", analyse_v7.compare_regional)
mixed_cash_budget = cast("Callable[..., list[dict[str, float]]]", equipment.mixed_cash_budget)
# Deliberately invalid values must be validated by the model itself.
_owned_asset = cast("Callable[..., OwnedAsset]", OwnedAsset)
_parameters = cast("Callable[..., Parameters]", Parameters)
_validate_estate = cast("Callable[..., None]", equipment.validate_estate)


def estate():
    return load_configuration(ROOT).owned_assets


def test_mixed_chhhs_initial_purchase_reconciles() -> None:
    s = portfolio("chhhs")
    rows = mixed_cash_budget(s, "panda", estate(), Parameters(), PathwaySpec(), retain=True)
    assert rows[0]["capital"] == 70000
    assert rows[2]["capital"] == 30000
    assert rows[5]["capital"] == 70000
    assert rows[0]["new_installations"] == 7


def test_new_purchase_does_not_use_sunk_estate() -> None:
    rows = mixed_cash_budget(portfolio("chhhs"), "panda", estate(), Parameters(), PathwaySpec(), retain=False)
    assert rows[0]["capital"] == 100000


def test_obsbot_does_not_inherit_panda_ownership() -> None:
    rows = mixed_cash_budget(portfolio("pilot"), "obsbot", estate(), Parameters(), PathwaySpec(), retain=True)
    assert rows[0]["capital"] == 13500


def test_cash_hub_capacity_not_double_counted() -> None:
    rows = mixed_cash_budget(portfolio("spokes"), "panda", estate(), Parameters(), PathwaySpec(), retain=True)
    for r in rows:
        assert r["cash_expenditure"] == pytest.approx(r["capital"] + r["cash_running"])


@pytest.mark.parametrize("remaining", [-1, True, 1.5, 100])
def test_invalid_owned_remaining_life_rejected(remaining: object) -> None:
    with pytest.raises(ValueError, match="Remaining life must be an integer between zero and fifty years"):
        # Deliberately invalid remaining-life values must fail closed.
        _ = _owned_asset("Atherton", "panda", remaining)


def test_duplicate_estate_records_rejected() -> None:
    m = equipment
    x = m.OwnedAsset("Atherton", "panda", 2)
    with pytest.raises(ValueError, match="Duplicate site in equipment estate"):
        _ = mixed_cash_budget(portfolio("pilot"), "panda", (x, x), Parameters(), PathwaySpec())


def test_configured_retention_matches_existing_pilot_and_regional_semantics() -> None:
    for net in ("pilot", "chhhs", "chhhs_tchhs", "spokes"):
        sites = portfolio(net)
        p = Parameters()
        s = PathwaySpec()
        old = compare_regional(sites, p, s, sunk=("panda",))
        current = compare_regional(sites, p, s, sunk=("panda",), owned_assets=estate())
        for arm in old:
            for field in old[arm]:
                np.testing.assert_allclose(old[arm][field], current[arm][field], rtol=1e-12, atol=1e-7)
        budget = mixed_cash_budget(sites, "panda", estate(), p, s, retain=True)
        assert current["panda"]["incremental_purchase_capital"][0] == pytest.approx(budget[0]["capital"])


def test_expired_asset_is_not_retained_without_purchase() -> None:
    m = equipment
    assets = (m.OwnedAsset("Atherton", "panda", 0),)
    r = compare_regional(portfolio("pilot"), Parameters(), PathwaySpec(), sunk=("panda",), owned_assets=assets)
    assert r["panda"]["incremental_purchase_capital"][0] == 30000


@pytest.mark.parametrize(("site", "strategy"), [("", "panda"), ("Atherton", "telephone"), ("Atherton", "unknown")])
def test_invalid_asset_identity(site: str, strategy: str) -> None:
    with pytest.raises(ValueError, match="Invalid asset site or configuration"):
        _ = equipment.OwnedAsset(site, strategy, 2)


@pytest.mark.parametrize(
    ("years", "retain", "life", "message"),
    [
        (0, True, 5, "Positive integer years and boolean retention required"),
        (True, True, 5, "Positive integer years and boolean retention required"),
        (7, "true", 5, "Positive integer years and boolean retention required"),
        (7, True, 2.5, "An explicit integer replacement interval is required"),
        (7, True, 1, "Remaining life exceeds configured equipment life"),
    ],
)
def test_bad_budget_contract(years: object, retain: object, life: object, message: str) -> None:
    with pytest.raises(ValueError, match=message):
        # Deliberately invalid years/retention/life values must fail closed.
        _ = mixed_cash_budget(
            portfolio("pilot"),
            "panda",
            estate(),
            _parameters(life_years=life),
            PathwaySpec(),
            years=years,
            retain=retain,
        )


def test_bad_estate_and_strategy_contracts() -> None:
    m = equipment
    with pytest.raises(ValueError, match="Estate requires OwnedAsset records"):
        # Deliberately wrong estate type must be rejected at runtime.
        _validate_estate(("not an asset",))
    with pytest.raises(ValueError, match="Unknown strategy"):
        _ = mixed_cash_budget(portfolio("pilot"), "invalid", estate(), Parameters(), PathwaySpec())
    with pytest.raises(ValueError, match="Invalid retained portfolio or strategies"):
        m.apply_retention({}, [], (), ())
