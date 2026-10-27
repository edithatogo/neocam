"""Local verification runner with explicit passed/failed/blocked statuses."""
from __future__ import annotations
import argparse
import ast
import csv
import hashlib
import importlib.metadata as metadata
import json
from pathlib import Path
import re
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
from src.statewide import load_sites, select_sites, Parameters, evaluate, psa


RELEASE_GATES = frozenset({
    'pytest', 'coverage_run', 'coverage_threshold', 'data_context_reproducibility',
    'ruff', 'generative_hypothesis', 'vulnerability_audit', 'hosted_GitHub_Actions',
    'latest_dependency_resolution', 'Conductor_working_tree',
})


def release_assurance_complete(gates: list[dict], scope: str) -> bool:
    """Release assurance needs explicit complete receipts, not a subset of checks."""
    statuses = {gate['gate']: gate['status'] for gate in gates}
    return (scope == 'release' and len(statuses) == len(gates)
            and RELEASE_GATES.issubset(statuses)
            and all(gate['status'] == 'passed' for gate in gates))


def command_receipt(name: str, command: list[str], timeout: int = 40) -> dict:
    try:
        result=subprocess.run(command,cwd=ROOT,capture_output=True,text=True,timeout=timeout,check=False)
        output=result.stdout+result.stderr
        status='passed' if result.returncode==0 else 'failed'
        if 'No module named' in output or 'Name or service not known' in output or 'Temporary failure in name resolution' in output:
            status='blocked'
        (ROOT/'verification'/f'{name}.txt').write_text(output)
        return {'gate':name,'status':status,'returncode':result.returncode,'command':command,'receipt':f'verification/{name}.txt'}
    except (subprocess.TimeoutExpired,FileNotFoundError) as error:
        return {'gate':name,'status':'blocked','command':command,'reason':str(error)}


def data_and_context_contract() -> list[str]:
    sites=load_sites()
    assert len(sites)==65 and sum(s.births for s in sites)==46711
    assert sum(s.births for s in select_sites(sites,'pilot'))==486
    params=Parameters(**json.loads((ROOT/'data/parameters.json').read_text()))
    assert evaluate(select_sites(sites,'pilot'),params)['consultations']==37.5
    assert len(select_sites(sites,'spokes'))==33
    sources=list(csv.DictReader((ROOT/'evidence/sources.csv').open()))
    assert len({s['source_id'] for s in sources})==len(sources)
    assert all(s['limitations'] and s['url'] for s in sources)
    for f in (ROOT/'src').glob('*.py'):
        ast.parse(f.read_text())
    ci=(ROOT/'.github/workflows/ci.yml').read_text()
    pins=re.findall(r'uses:\s*([^\s]+)',ci)
    assert all(re.search(r'@[a-f0-9]{40}$',pin) for pin in pins)
    assert 'contents: read' in ci and 'persist-credentials: false' in ci
    assert 'pull_request_target' not in ci
    assert 'submodules: true' in ci
    assert (ROOT/'AGENTS.md').exists()
    state=json.loads((ROOT/'conductor/current-state.json').read_text())
    assert state['active_track']=='panda-vision-v2-statewide-assurance'
    # Same process + same seed must reproduce, without network or patient records.
    one=psa(select_sites(sites,'pilot'),500,20261027,params)
    two=psa(select_sites(sites,'pilot'),500,20261027,params)
    assert one['summary']==two['summary']
    return ['birth counts/aliases','parameter schema','source uniqueness/provenance','Python AST','immutable action pins','least privilege','context entrypoint','seeded reproducibility']


def main() -> int:
    parser=argparse.ArgumentParser()
    parser.add_argument('--ci',action='store_true')
    args=parser.parse_args()
    (ROOT/'verification').mkdir(exist_ok=True)
    gates=[command_receipt('pytest',[sys.executable,'-m','pytest','-q']),
           command_receipt('coverage_run',[sys.executable,'-m','coverage','run','--branch','--source=src.statewide','-m','pytest','-q']),
           command_receipt('coverage_threshold',[sys.executable,'-m','coverage','report','--fail-under=95'])]
    try:
        checks=data_and_context_contract()
        gates.append({'gate':'data_context_reproducibility','status':'passed','checks':checks})
    except Exception as error:
        gates.append({'gate':'data_context_reproducibility','status':'failed','reason':repr(error)})
    if not args.ci:
        for name,cmd in [('ruff',[sys.executable,'-m','ruff','check','src','scripts/run_v2.py','scripts/verify.py']),
                         ('generative_hypothesis',[sys.executable,'-m','pytest','quality/property_hypothesis.py','-q']),
                         ('vulnerability_audit',[sys.executable,'-m','pip_audit','-r','requirements-latest.in']),
                         ('typecheck_experimental',[sys.executable,'-m','ty','check','src/statewide.py'])]:
            gates.append(command_receipt(name,cmd))
        gates.append({'gate':'hosted_GitHub_Actions','status':'blocked','reason':'No hosted run triggered; project has no specified GitHub remote. Local receipt is not hosted CI evidence.'})
        gates.append({'gate':'latest_dependency_resolution','status':'blocked','reason':'External DNS unavailable; target pins verified remotely, installation/hash-lock resolution not completed.'})
        status=subprocess.run(['git','submodule','status'],cwd=ROOT,capture_output=True,text=True,check=False).stdout.strip()
        gates.append({'gate':'Conductor_working_tree','status':'passed' if (ROOT/'extensions/conductor/README.md').exists() else 'blocked','evidence':status})
    environment={'python':sys.version,'packages':{}}
    for name in ['numpy','pytest','coverage','ruff','hypothesis','pip-audit','ty','uv','python-docx','python-pptx','matplotlib']:
        try:environment['packages'][name]=metadata.version(name)
        except metadata.PackageNotFoundError:environment['packages'][name]=None
    hashes={str(f.relative_to(ROOT)):hashlib.sha256(f.read_bytes()).hexdigest()
            for parent in ['src','data','evidence'] for f in sorted((ROOT/parent).glob('*')) if f.is_file()}
    report={'date':'2026-10-27','environment':environment,'gates':gates,'source_sha256':hashes,
            'all_available_gates_pass':not any(g['status']=='failed' for g in gates),
            'full_release_assurance':release_assurance_complete(gates,'model'),
            'receipt_scope':'model/data gates only; hosted workflow and release require separate receipts',
            'review':'Author self-review; no independent agent reviewer available'}
    (ROOT/'verification/assurance.json').write_text(json.dumps(report,indent=2)+'\n')
    for gate in gates:print(gate['status'].upper(),gate['gate'])
    return int(any(g['status']=='failed' for g in gates))


if __name__=='__main__':
    raise SystemExit(main())
