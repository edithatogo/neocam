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


def test_configured_retention_matches_existing_pilot_and_regional_semantics():
    m=api()
    from src.statewide import _base_arrays
    from scripts.analyse_v7 import compare_regional
    import numpy as np
    for net in ('pilot','chhhs','chhhs_tchhs','spokes'):
        sites=portfolio(net);p=Parameters();s=PathwaySpec()
        old=compare_regional(sites,p,s,sunk=('panda',))
        current=compare_regional(sites,p,s,sunk=('panda',),owned_assets=estate())
        for arm in old:
            for field in old[arm]:np.testing.assert_allclose(old[arm][field],current[arm][field],rtol=1e-12,atol=1e-7)
        budget=m.mixed_cash_budget(sites,'panda',estate(),p,s,retain=True)
        assert current['panda']['incremental_purchase_capital'][0]==pytest.approx(budget[0]['capital'])


def test_expired_asset_is_not_retained_without_purchase():
    m=api();from scripts.analyse_v7 import compare_regional
    assets=(m.OwnedAsset('Atherton','panda',0),)
    r=compare_regional(portfolio('pilot'),Parameters(),PathwaySpec(),sunk=('panda',),owned_assets=assets)
    assert r['panda']['incremental_purchase_capital'][0]==30000


@pytest.mark.parametrize('site,strategy',[('', 'panda'),('Atherton','telephone'),('Atherton','unknown')])
def test_invalid_asset_identity(site,strategy):
    with pytest.raises(ValueError):api().OwnedAsset(site,strategy,2)


@pytest.mark.parametrize('years,retain,life',[ (0,True,5),(True,True,5),(7,'true',5),(7,True,2.5),(7,True,1)])
def test_bad_budget_contract(years,retain,life):
    with pytest.raises(ValueError):api().mixed_cash_budget(portfolio('pilot'),'panda',estate(),Parameters(life_years=life),PathwaySpec(),years=years,retain=retain)


def test_bad_estate_and_strategy_contracts():
    m=api()
    with pytest.raises(ValueError):m.validate_estate(('not an asset',))
    with pytest.raises(ValueError):m.mixed_cash_budget(portfolio('pilot'),'invalid',estate(),Parameters(),PathwaySpec())
    with pytest.raises(ValueError):m.apply_retention({},[],(),())
