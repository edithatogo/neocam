"""Run the actual analysis CLI using a modified declared scenario."""
import csv
import json
import os
from pathlib import Path
import shutil
import subprocess
import sys
import pytest
ROOT=Path(__file__).resolve().parents[1]


def test_real_entrypoint_consumes_configuration_and_preserves_old_outputs(tmp_path):
    def trace(stage):
        with (tmp_path/'trace.txt').open('a') as f:f.write(stage+'\n')
    trace('started')
    for name in ('src','scripts','config','data'):
        shutil.copytree(ROOT/name,tmp_path/name,ignore=shutil.ignore_patterns('__pycache__'))
    p=tmp_path/'data/parameters.json';d=json.loads(p.read_text());d['equipment_cost']=20000;p.write_text(json.dumps(d))
    f=tmp_path/'config/reference.json';d=json.loads(f.read_text());d['run']['draws']=32;d['run']['portfolios']=['pilot'];f.write_text(json.dumps(d))
    trace('before first subprocess')
    result=subprocess.run([sys.executable,'-m','scripts.analyse_v7','--config','config/reference.json','--output','outputs/check'],cwd=tmp_path,capture_output=True,text=True,timeout=90,env=os.environ.copy())
    trace('first returned '+str(result.returncode))
    assert result.returncode==0,result.stderr
    target=tmp_path/'outputs/check'
    assert target.is_dir(), 'Driver did not honour the output argument'
    with (target/'deterministic.csv').open() as stream:
        values=list(csv.DictReader(stream))
    assert next(r for r in values if r['strategy']=='panda')['sites']=='3'
    inputs=json.loads((target/'resolved_inputs.json').read_text())
    assert inputs['parameters']['equipment_cost']==20000
    assert json.loads((target/'results.json').read_text())['draws']==32
    with (target/'utility_bridge_scenarios.csv').open() as stream:
        utility=list(csv.DictReader(stream))
    r=next(r for r in utility if float(r['utility_difference'])==.13 and int(r['duration_years_assumed'])==1 and float(r['discount_rate'])==.05 and float(r['fraction_consultations_improved_assumed'])==.001)
    assert float(r['qalys_per_1000_consultations'])==pytest.approx(.13/1.05**11)
    assert (target/'mixed_estate_budget.csv').exists()
    assert (target/'prior_predictive.csv').exists()
    trace('before overwrite refusal')
    rerun=subprocess.run([sys.executable,'-m','scripts.analyse_v7','--output','outputs/check'],cwd=tmp_path,capture_output=True,text=True,timeout=15)
    trace('second returned '+str(rerun.returncode))
    assert rerun.returncode!=0, 'Existing release was silently overwritten'
