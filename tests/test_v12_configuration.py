"""Declared inputs must reach the executed analysis, not merely agree with a register."""
import importlib
import importlib.util
import json
from dataclasses import asdict
from pathlib import Path
import shutil

import pytest
from src.statewide import Parameters
from src.pathways_v6 import PathwaySpec
ROOT=Path(__file__).resolve().parents[1]


def api():
    assert importlib.util.find_spec('src.configuration'), 'Missing resolved configuration interface'
    return importlib.import_module('src.configuration')


def fixture(tmp_path):
    assert (ROOT/'config').is_dir(), 'Missing authoritative run configuration'
    shutil.copytree(ROOT/'config',tmp_path/'config')
    shutil.copytree(ROOT/'data',tmp_path/'data')
    return tmp_path


def test_default_resolved_values_preserve_reference():
    c=api().load_configuration(ROOT)
    assert asdict(c.parameters)==asdict(Parameters())
    assert asdict(c.pathways)==asdict(PathwaySpec())
    assert len(c.owned_assets)==3


def test_changed_declared_price_reaches_driver(tmp_path):
    m=api();root=fixture(tmp_path)
    path=root/'data/parameters.json';d=json.loads(path.read_text());d['equipment_cost']=20000.;path.write_text(json.dumps(d))
    c=m.load_configuration(root)
    from scripts.analyse_v7 import evaluate_perspectives
    from src.statewide import _base_arrays
    from src.portfolios_v7 import portfolio
    r,_,_=evaluate_perspectives(portfolio('pilot'),c.parameters,c.pathways,_base_arrays(c.parameters,1),{},owned_assets=c.owned_assets)
    assert r['panda']['incremental_purchase_capital'][0]==60000
    assert c.snapshot()['parameters']['equipment_cost']==20000


@pytest.mark.parametrize('change',[{'draws':True},{'seed':-1},{'portfolios':['pilot','pilot']},{'unknown':1}])
def test_bad_run_config_rejected(tmp_path,change):
    m=api();root=fixture(tmp_path);path=root/'config/reference.json'
    d=json.loads(path.read_text());d['run'].update(change);path.write_text(json.dumps(d))
    with pytest.raises(ValueError):m.load_configuration(root)


def test_duplicate_json_keys_rejected(tmp_path):
    m=api();root=fixture(tmp_path);(root/'config/pathways.json').write_text('{"endpoint":"eventual","endpoint":"initial"}')
    with pytest.raises(ValueError):m.load_configuration(root)


def test_partial_pathway_document_cannot_silently_default(tmp_path):
    m=api();root=fixture(tmp_path);(root/'config/pathways.json').write_text('{"endpoint":"initial"}')
    with pytest.raises(ValueError):m.load_configuration(root)


def test_source_escape_rejected(tmp_path):
    m=api();root=fixture(tmp_path);path=root/'config/reference.json';d=json.loads(path.read_text());d['parameters']='../escape.json';path.write_text(json.dumps(d))
    with pytest.raises(ValueError):m.load_configuration(root)


def test_configuration_hash_changes_with_live_pathway(tmp_path):
    m=api();root=fixture(tmp_path);a=m.load_configuration(root)
    path=root/'config/pathways.json';d=json.loads(path.read_text());d['hub_minutes_per_call']=30;path.write_text(json.dumps(d));b=m.load_configuration(root)
    assert a.digest!=b.digest and b.pathways.hub_minutes_per_call==30


@pytest.mark.parametrize('which,value',[('root',[]),('schema',2),('assets',None),('asset_record',{'site':'Atherton'}),('path','/absolute'),('remaining',6),('nonfinite',float('nan'))])
def test_other_malformed_configuration_contracts(tmp_path,which,value):
    m=api();root=fixture(tmp_path);f=root/'config/reference.json';d=json.loads(f.read_text())
    if which=='root':f.write_text(json.dumps(value))
    elif which=='schema':d['schema_version']=value;f.write_text(json.dumps(d))
    elif which=='path':d['parameters']=value;f.write_text(json.dumps(d))
    elif which=='nonfinite':
        p=root/'data/parameters.json';v=json.loads(p.read_text());v['equipment_cost']=value;p.write_text(json.dumps(v))
    else:
        p=root/'config/equipment_estate.json';v=json.loads(p.read_text())
        if which=='assets':v['owned_assets']=value
        elif which=='asset_record':v['owned_assets']=[value]
        else:v['owned_assets'][0]['remaining_life_years']=value
        p.write_text(json.dumps(v))
    with pytest.raises(ValueError):m.load_configuration(root)


def test_run_recipe_outside_repository_rejected(tmp_path):
    with pytest.raises(ValueError):api().load_configuration(tmp_path,tmp_path.parent/'elsewhere.json')


def test_misspelled_owned_site_cannot_silently_disappear(tmp_path):
    m=api();root=fixture(tmp_path);f=root/'config/equipment_estate.json';d=json.loads(f.read_text());d['owned_assets'][0]['site']='Athertonn';f.write_text(json.dumps(d))
    with pytest.raises(ValueError):m.load_configuration(root)
