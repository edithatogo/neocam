"""Test runner/control boundaries with real child processes and isolated fixtures.

Mocks below simulate download/environment metadata to test error handling only;
these tests are not evidence that any external linter/scanner has executed.
"""
from pathlib import Path
from types import SimpleNamespace
import io
import json
import sys
import urllib.error
import pytest

from quality import cli, checks, assurance, bootstrap
from quality.assurance import Gate, run_gate
from tests.test_quality_gates import binary_tar, mutation_report


def context_fixture(root):
    (root/'conductor').mkdir()
    (root/'.github/workflows').mkdir(parents=True)
    for name in ['AGENTS.md','GEMINI.md']:
        (root/name).write_text('See conductor/runbook.md')
    for name in ['runbook.md','tracks.md','decisions-v3.md']:
        (root/'conductor'/name).write_text('Context')
    (root/'conductor/current-state.json').write_text('{"release_ready":false,"active_tracks":[]}')


def test_clean_context_fixture(tmp_path):
    context_fixture(tmp_path)
    assert checks.context_errors(tmp_path)==[]


@pytest.mark.parametrize('change', ['entry','oversized','track','state','reference','pin','bypass'])
def test_context_regressions_rejected(tmp_path,change):
    context_fixture(tmp_path)
    if change=='entry':(tmp_path/'AGENTS.md').unlink()
    elif change=='oversized':(tmp_path/'AGENTS.md').write_text('conductor/runbook.md'+'x'*6001)
    elif change=='track':(tmp_path/'conductor/current-state.json').write_text('{"release_ready":false,"active_tracks":["missing"]}')
    elif change=='state':(tmp_path/'conductor/current-state.json').write_text('{"release_ready":true}')
    elif change=='reference':(tmp_path/'conductor/runbook.md').unlink()
    elif change=='pin':(tmp_path/'.github/workflows/a.yml').write_text('uses: actions/checkout@main')
    else:(tmp_path/'.github/workflows/a.yml').write_text('pull_request_target:')
    assert checks.context_errors(tmp_path)


def invoke_check(monkeypatch,root,name):
    monkeypatch.setattr(checks,'ROOT',root)
    monkeypatch.setattr(sys,'argv',['checks',name])
    return checks.main()


@pytest.mark.parametrize('name', ['lock','mutation','scalene_output'])
def test_missing_prerequisite_returns_unavailable(monkeypatch,tmp_path,name):
    assert invoke_check(monkeypatch,tmp_path,name)==69


def test_inputs_command_reconciles_real_inputs(monkeypatch):
    root=Path(__file__).resolve().parents[1]
    assert invoke_check(monkeypatch,root,'inputs')==0


def test_context_command(monkeypatch,tmp_path):
    context_fixture(tmp_path)
    assert invoke_check(monkeypatch,tmp_path,'context')==0


def test_invalid_existing_lock_is_failure(monkeypatch,tmp_path):
    (tmp_path/'uv.lock').write_text('version=1')
    assert invoke_check(monkeypatch,tmp_path,'lock')==1


@pytest.mark.parametrize('valid',[True,False])
def test_mutation_command_checks_report(monkeypatch,tmp_path,valid):
    folder=tmp_path/'coverage/gremlins';folder.mkdir(parents=True)
    (folder/'gremlins.json').write_text(json.dumps(mutation_report(90 if valid else 80,10 if valid else 20)))
    assert invoke_check(monkeypatch,tmp_path,'mutation')==int(not valid)


@pytest.mark.parametrize('valid',[True,False])
def test_scalene_report_cannot_be_empty(monkeypatch,tmp_path,valid):
    folder=tmp_path/'verification/v7';folder.mkdir(parents=True)
    (folder/'scalene.json').write_text(json.dumps({'files':{'src/statewide.py':{}}} if valid else {}))
    assert invoke_check(monkeypatch,tmp_path,'scalene_output')==int(not valid)


@pytest.mark.parametrize('state',['missing','wrong','ok'])
def test_submodule_requires_checkout_and_pin(monkeypatch,tmp_path,state):
    if state!='missing':
        folder=tmp_path/'extensions/conductor';folder.mkdir(parents=True)
        (folder/'README.md').write_text('test checkout')
    output=('+bad extensions/conductor\n' if state=='wrong' else ' abc extensions/conductor\n')
    monkeypatch.setattr(checks.subprocess,'run',lambda *args,**kwargs: SimpleNamespace(returncode=0,stdout=output,stderr=''))
    assert invoke_check(monkeypatch,tmp_path,'submodule')==({'missing':69,'wrong':1,'ok':0}[state])


def test_shared_host_not_treated_as_project_environment(monkeypatch, tmp_path):
    root=Path(__file__).resolve().parents[1]
    monkeypatch.setattr(checks.sys, 'prefix', str(tmp_path / 'host-environment'))
    errors=checks.version_errors(root)
    assert any('project .venv' in item for item in errors)
    assert not any('Prohibited installed' in item for item in errors)


def test_versions_command_explicit_blocker(monkeypatch,tmp_path):
    monkeypatch.setattr(checks,'version_errors',lambda root:['required package missing'])
    assert invoke_check(monkeypatch,tmp_path,'versions')==69


def test_versions_command_pass_path(monkeypatch,tmp_path):
    monkeypatch.setattr(checks,'version_errors',lambda root:[])
    assert invoke_check(monkeypatch,tmp_path,'versions')==0


def test_explicit_preflight_may_report_unavailable(tmp_path):
    gate=Gate('preflight',(sys.executable,'-c','raise SystemExit(69)'),allow_unavailable=True)
    assert run_gate(gate,tmp_path,'abc',tmp_path/'logs').status=='blocked'


def test_invalid_module_spec_is_blocked(monkeypatch,tmp_path):
    def fail(name):raise ImportError('unavailable')
    monkeypatch.setattr(assurance.importlib.util,'find_spec',fail)
    assert run_gate(Gate('probe',('unused',),module='missing'),tmp_path,'abc',tmp_path/'logs').status=='blocked'


@pytest.mark.parametrize('exitcode',[0,1,69])
def test_cli_exit_matches_actual_child_and_never_implies_release(monkeypatch,tmp_path,exitcode):
    monkeypatch.setattr(cli,'ROOT',tmp_path)
    monkeypatch.setattr(sys,'argv',['cli','--profile','quick'])
    monkeypatch.setattr(cli,'gates_for_profile',lambda profile:[Gate('probe',(sys.executable,'-c',f'raise SystemExit({exitcode})'))])
    assert cli.main()==int(exitcode!=0)
    report=json.loads((tmp_path/'verification/v7/quick/receipt.json').read_text())
    assert report['release_ready'] is False
    assert report['full_local_assurance'] is False
    assert report['complete_within_profile']==(exitcode==0)


def test_cli_detects_mid_run_change(monkeypatch,tmp_path):
    (tmp_path/'src').mkdir()
    monkeypatch.setattr(cli,'ROOT',tmp_path)
    monkeypatch.setattr(sys,'argv',['cli','--profile','quick'])
    program='from pathlib import Path; Path("src/new.py").write_text("value=1")'
    monkeypatch.setattr(cli,'gates_for_profile',lambda profile:[Gate('probe',(sys.executable,'-c',program))])
    assert cli.main()==1


def test_full_cli_removes_old_reports_before_execution(monkeypatch,tmp_path):
    folder=tmp_path/'coverage/gremlins';folder.mkdir(parents=True)
    (folder/'gremlins.json').write_text('old')
    monkeypatch.setattr(cli,'ROOT',tmp_path)
    monkeypatch.setattr(sys,'argv',['cli','--profile','full'])
    monkeypatch.setattr(cli,'gates_for_profile',lambda profile:[Gate('probe',(sys.executable,'-c','raise SystemExit(1)'))])
    assert cli.main()==1
    assert not (folder/'gremlins.json').exists()


def test_project_environment_rejects_forbidden_installed_package(monkeypatch, tmp_path):
    root=Path(__file__).resolve().parents[1]
    monkeypatch.setattr(checks.sys,'prefix',str(root/'.venv'))
    monkeypatch.setattr(checks.importlib.metadata,'distributions',lambda:[SimpleNamespace(metadata={'Name':'pandas'}),SimpleNamespace(metadata={'Name':''})])
    errors=checks.version_errors(root)
    assert not any('shared host environment' in item for item in errors)
    assert any('Prohibited installed dependency: pandas' in item for item in errors)
