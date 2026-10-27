"""Exercise malformed evidence and boundary cases rather than only happy paths."""
from dataclasses import replace
from pathlib import Path
import csv
import json
import math
import shutil
import pytest

from quality.contracts import audit_inputs, validate_lock, _same_value
from src.statewide import Parameters, Site, load_sites, survival_extension
from src.panda_model import ModelInputs, odds_to_probability, weighted_transfer_cost, clinical_extension

ROOT=Path(__file__).resolve().parents[1]


def evidence_copy(tmp_path):
    shutil.copytree(ROOT/'data',tmp_path/'data')
    shutil.copytree(ROOT/'evidence',tmp_path/'evidence')
    return tmp_path


def update_csv(path, mutate):
    with path.open(newline='',encoding='utf-8') as stream:
        reader=csv.DictReader(stream)
        fields=reader.fieldnames
        rows=list(reader)
    mutate(rows)
    with path.open('w',newline='',encoding='utf-8') as stream:
        writer=csv.DictWriter(stream,fieldnames=fields)
        writer.writeheader()
        writer.writerows(rows)


@pytest.mark.parametrize('field,value', [('base_value','999'),('uncertainty',''),('interpretation',''),('source_ids','UNKNOWN_EVIDENCE')])
def test_parameter_register_corruption_rejected(tmp_path,field,value):
    root=evidence_copy(tmp_path)
    update_csv(root/'evidence/parameter_register.csv',lambda rows: rows[0].update({field:value}))
    assert audit_inputs(root)['errors']


def test_duplicate_parameter_rejected(tmp_path):
    root=evidence_copy(tmp_path)
    update_csv(root/'evidence/parameter_register.csv',lambda rows: rows.append(rows[0].copy()))
    assert audit_inputs(root)['errors']


@pytest.mark.parametrize('field', ['url','limitations'])
def test_source_disclosure_cannot_be_missing(tmp_path,field):
    root=evidence_copy(tmp_path)
    update_csv(root/'evidence/sources.csv',lambda rows: rows[0].update({field:''}))
    assert audit_inputs(root)['errors']


def test_duplicate_source_rejected(tmp_path):
    root=evidence_copy(tmp_path)
    update_csv(root/'evidence/sources.csv',lambda rows: rows.append(rows[0].copy()))
    assert audit_inputs(root)['errors']


@pytest.mark.parametrize('field', ['public_births','raw_public_rows','total','year'])
def test_bad_denominator_metadata_rejected(tmp_path,field):
    root=evidence_copy(tmp_path)
    path=root/'data/population_totals.json'
    data=json.loads(path.read_text());data[field]+=1
    path.write_text(json.dumps(data))
    assert audit_inputs(root)['errors']


def test_missing_parameter_not_silently_defaulted_in_audit(tmp_path):
    root=evidence_copy(tmp_path)
    path=root/'data/parameters.json'
    data=json.loads(path.read_text());data.pop('equipment_cost')
    path.write_text(json.dumps(data))
    assert audit_inputs(root)['errors']


@pytest.mark.parametrize('text', ['[invalid', 'package=[1]', '[[package]]\nname="a"\nsource="wrong"',
    '[[package]]\nname="a"\nsource={registry="x"}\nsdist={hash="bad"}',
    '[[package]]\nname="a"\nsource={registry="x"}\nwheels=[3]'])
def test_malformed_lock_fail_closed(tmp_path,text):
    path=tmp_path/'uv.lock';path.write_text(text)
    assert validate_lock(path)


def test_sdist_hash_is_supported(tmp_path):
    path=tmp_path/'uv.lock'
    path.write_text('[[package]]\nname="a"\nsource={registry="x"}\nsdist={hash="sha256:'+'a'*64+'"}')
    assert validate_lock(path)==[]


def test_value_comparison_distinguishes_strings_and_booleans():
    assert _same_value('label','label')
    assert not _same_value(True,1)
    assert not _same_value([1],[1,2])


@pytest.mark.parametrize('change', [{'name':''},{'births':1.2},{'year':1800},{'group':'unknown'}, {'geography':'unknown'},{'pilot':1}])
def test_site_boundary_validation(change):
    values={'name':'Test','births':1,'year':2022,'group':'rural_proxy','geography':'regional'}
    with pytest.raises(ValueError):
        Site(**(values|change))


@pytest.mark.parametrize('change', [{'case_mix':'bad'},{'case_mix':(True,0,0)}, {'life_years':0},
    {'support':-1},{'case_mix':(.5,.5)},{'case_mix':(.3,.3,.3)}, {'baseline_transfer':(.3,.6,2)}, {'mode_air_shift':.7}])
def test_parameter_boundary_validation(change):
    with pytest.raises(ValueError):
        Parameters(**change)


@pytest.mark.parametrize('text', ['wrong,column\nA,1\n','facility,births,year,sector\nA,1,2022,private\n',
    'facility,births,year\nA,-1,2022\n'])
def test_malformed_birth_rows_fail(tmp_path,text):
    path=tmp_path/'births.csv';path.write_text(text)
    with pytest.raises(ValueError):
        load_sites(path)


def test_survival_cost_cannot_be_negative():
    with pytest.raises(ValueError):
        survival_extension(1,.1,.5,annual_cost_major=-1)


@pytest.mark.parametrize('probability,odds', [(-.1,1),(.5,0)])
def test_legacy_probability_error_paths(probability,odds):
    with pytest.raises(ValueError):
        odds_to_probability(probability,odds)


@pytest.mark.parametrize('probability',[0,1])
def test_legacy_probability_endpoints(probability):
    assert odds_to_probability(probability,.5)==probability


def test_legacy_transport_rejects_non_normalized_mix():
    with pytest.raises(ValueError):
        weighted_transfer_cost(replace(ModelInputs(),road_share=1))


def test_legacy_survival_arithmetic():
    result=clinical_extension(100,.01,.1)
    assert result['extra_survivors']==1
    assert math.isclose(result['incremental_qalys'],23.3)
    assert result['incremental_lifetime_costs']==95000
