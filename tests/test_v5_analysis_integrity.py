"""Output lineage and separation of clinical evidence from explanatory learning."""
import hashlib
import importlib.util
import json
from pathlib import Path
import numpy as np
ROOT=Path(__file__).resolve().parents[1]


def test_analysis_manifest_excludes_its_own_mutating_digest(tmp_path):
    spec=importlib.util.spec_from_file_location('analysis_v5',ROOT/'scripts/analyse_v5.py')
    module=importlib.util.module_from_spec(spec);spec.loader.exec_module(module)
    d=tmp_path/'outputs';d.mkdir();(d/'table.csv').write_text('x\n1\n')
    (d/'analysis_manifest.json').write_text('{}')
    module.write_manifest(d,root=tmp_path)
    first=(d/'analysis_manifest.json').read_bytes()
    module.write_manifest(d,root=tmp_path)
    assert first==(d/'analysis_manifest.json').read_bytes()
    payload=json.loads(first)
    assert not any(k.endswith('analysis_manifest.json') for k in payload)
    assert payload['outputs/table.csv']==hashlib.sha256((d/'table.csv').read_bytes()).hexdigest()


def test_recorded_five_arm_results_retain_v4_panda():
    r=json.loads((ROOT/'outputs/v5/results_v5.json').read_text())
    assert all(r['protected_v4_result_parity'].values())
    assert r['psa_primary_structures']==18
    assert r['psa_iterations_each']==20000
    for result in r['psa'].values():
        assert np.isclose(sum(v['p_optimal'] for v in result['summary'].values()),1)
        assert result['cost_only_evpi']>=0


def test_all_recorded_analysis_hashes_are_current():
    manifest=json.loads((ROOT/'outputs/v5/analysis_manifest.json').read_text())
    assert not any(k.endswith('analysis_manifest.json') for k in manifest)
    for name,digest in manifest.items():
        assert hashlib.sha256((ROOT/name).read_bytes()).hexdigest()==digest,name
