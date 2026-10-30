"""Economic retention and purchases must describe the same mixed equipment estate."""
import importlib
import importlib.util
from pathlib import Path
import pytest
from src.statewide import Parameters
from src.pathways_v6 import PathwaySpec
from src.portfolios_v7 import portfolio
ROOT=Path(__file__).resolve().parents[1]


def api():
    assert importlib.util.find_spec('src.equipment'), 'Missing mixed-estate budget interface'
    return importlib.import_module('src.equipment')


def estate():
    from src.configuration import load_configuration
    return load_configuration(ROOT).owned_assets


def test_mixed_chhhs_initial_purchase_reconciles():
    m=api();s=portfolio('chhhs');rows=m.mixed_cash_budget(s,'panda',estate(),Parameters(),PathwaySpec(),retain=True)
    assert rows[0]['capital']==70000
    assert rows[2]['capital']==30000
    assert rows[5]['capital']==70000
    assert rows[0]['new_installations']==7


def test_new_purchase_does_not_use_sunk_estate():
    m=api();rows=m.mixed_cash_budget(portfolio('chhhs'),'panda',estate(),Parameters(),PathwaySpec(),retain=False)
    assert rows[0]['capital']==100000


def test_obsbot_does_not_inherit_panda_ownership():
    m=api();rows=m.mixed_cash_budget(portfolio('pilot'),'obsbot',estate(),Parameters(),PathwaySpec(),retain=True)
    assert rows[0]['capital']==13500


def test_cash_hub_capacity_not_double_counted():
    m=api();rows=m.mixed_cash_budget(portfolio('spokes'),'panda',estate(),Parameters(),PathwaySpec(),retain=True)
    for r in rows:assert r['cash_expenditure']==pytest.approx(r['capital']+r['cash_running'])


@pytest.mark.parametrize('remaining',[-1,True,1.5,100])
def test_invalid_owned_remaining_life_rejected(remaining):
    m=api()
    with pytest.raises(ValueError):m.OwnedAsset('Atherton','panda',remaining)


def test_duplicate_estate_records_rejected():
    m=api();x=m.OwnedAsset('Atherton','panda',2)
    with pytest.raises(ValueError):m.mixed_cash_budget(portfolio('pilot'),'panda',(x,x),Parameters(),PathwaySpec())
