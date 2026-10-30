"""Real entrypoint for refinements: resolved inputs, eligibility and safe exports."""
import csv
import importlib
import json
from pathlib import Path
import shutil
import subprocess
import sys
import numpy as np
import pytest
ROOT=Path(__file__).resolve().parents[1]


def test_catalogue_deduplicates_identical_pilot_policies():
    from src.deployment import policy_catalogue
    from src.portfolios_v7 import portfolio
    policies=policy_catalogue(portfolio('pilot'))
    assert len({p.assignments for p in policies})==len(policies)
    assert len(policies)==2


def test_refinement_schema_is_strict(tmp_path):
    from scripts.analyse_refinements import load_refinements
    data=json.loads((ROOT/'config/refinements.json').read_text())
    p=tmp_path/'refinements.json';p.write_text(json.dumps(data))
    assert load_refinements(p)['schema_version']==1
    data['unexpected']=1;p.write_text(json.dumps(data))
    with pytest.raises(ValueError):load_refinements(p)


def test_real_refinement_pipeline(tmp_path):
    assert (ROOT/'scripts/analyse_refinements.py').exists()
    for folder in ('src','scripts','quality','config','data'):
        shutil.copytree(ROOT/folder,tmp_path/folder,ignore=shutil.ignore_patterns('__pycache__'))
    f=tmp_path/'config/reference.json';data=json.loads(f.read_text());data['run'].update(draws=32,portfolios=['pilot','chhhs']);f.write_text(json.dumps(data))
    result=subprocess.run([sys.executable,'-m','scripts.analyse_refinements','--output','outputs/check'],cwd=tmp_path,capture_output=True,text=True,timeout=45)
    assert result.returncode==0,result.stderr
    folder=tmp_path/'outputs/check'
    metadata=json.loads((folder/'results.json').read_text())
    assert metadata['draws']==32
    assert metadata['independent_validation'] is False
    assert metadata['max_cohort_residual']<1e-7
    assert metadata['all_finite'] is True
    def rows(name):
        with (folder/name).open() as f:return list(csv.DictReader(f))
    table=rows('policy_deterministic.csv')
    row=next(r for r in table if r['portfolio']=='chhhs' and r['policy']=='retain_pilot_expand_obsbot' and r['activity_id']=='contacts_1')
    assert float(row['initial_purchase_capital'])==31500
    assert row['conditional_policy']=='True'
    reported=rows('policy_rankings.csv')
    assert all(r['policy'] in ('telephone','retain_pilot_only') for r in reported if r['decision_set']=='reported_operation')
    assert all(0<=float(r['probability_optimal'])<=1 for r in reported)
    checks=json.loads((folder/'review_packet.json').read_text())
    assert all(r['status']=='pending' for r in checks['reviews'])
    snapshot=json.loads((folder/'resolved_inputs.json').read_text())
    assert 'refinements_sha256' in snapshot
    # Shared reference is not overwritten or compared as an empirical observation.
    assert (folder/'policy_predictive.csv').exists()
    assert (folder/'policy_budget.csv').exists()
    assert (folder/'eligibility.csv').exists()
    assert (folder/'policy_assignments.csv').exists()
    refusal=subprocess.run([sys.executable,'-m','scripts.analyse_refinements','--output','outputs/check'],cwd=tmp_path,capture_output=True,text=True,timeout=10)
    assert refusal.returncode!=0


def test_new_driver_enters_artifact_dependency_manifest(tmp_path):
    from quality.artifacts import calculation_inputs
    (tmp_path/'scripts').mkdir()
    p=tmp_path/'scripts/analyse_refinements.py';p.write_text('#one')
    first=calculation_inputs(tmp_path)
    assert 'scripts/analyse_refinements.py' in first
    p.write_text('#two')
    assert calculation_inputs(tmp_path)!=first
