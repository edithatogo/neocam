"""Regression checks for truthful acceptance and installed-plugin execution."""
import hashlib
from pathlib import Path
import sys

from quality.assurance import Receipt, input_fingerprint, validate_receipts
from quality.cli import gates_for_profile


def passed(root: Path, gate: str = 'tests') -> Receipt:
    log = root / 'log.txt'
    log.write_text('passed\n')
    return Receipt(gate, 'passed', 0, 'fp', (sys.executable, '-m', 'pytest'), .1,
                   'log.txt', hashlib.sha256(log.read_bytes()).hexdigest())


def test_empty_acceptance_scope_is_never_success(tmp_path):
    assert validate_receipts([], set(), 'fp', tmp_path)


def test_unexpected_gate_cannot_expand_acceptance_scope(tmp_path):
    assert validate_receipts([passed(tmp_path)], {'tests', 'inputs'}, 'fp', tmp_path)
    assert validate_receipts([passed(tmp_path, 'extra')], set(), 'fp', tmp_path)


def test_gitmodules_changes_invalidate_assurance(tmp_path):
    path = tmp_path / '.gitmodules'
    path.write_text('[submodule "conductor"]\n path = extensions/conductor\n url = https://github.com/edithatogo/conductor-next.git\n')
    first = input_fingerprint(tmp_path)
    path.write_text(path.read_text().replace('conductor-next', 'different-project'))
    assert input_fingerprint(tmp_path) != first


def test_empty_directory_does_not_equal_submodule_pin(tmp_path):
    root = tmp_path / 'extensions'
    root.mkdir()
    before = input_fingerprint(tmp_path)
    (tmp_path / '.gitmodules').write_text('[submodule "c"]\n path = extensions/c\n')
    assert input_fingerprint(tmp_path) != before


def test_mutation_loads_required_plugin_explicitly():
    cmd = next(g.command for g in gates_for_profile('full') if g.name == 'gremlins')
    assert ('-p', 'gremlins') in tuple(zip(cmd, cmd[1:]))


def test_compatibility_installs_research_dependencies():
    text = Path('.github/workflows/ci.yml').read_text().split('  compatibility:', 1)[1]
    assert 'uv sync --frozen --group test --extra research' in text


def test_incremental_testmon_loads_plugin_explicitly(tmp_path):
    from quality.feedback import prepare
    plan = prepare(tmp_path, 'tests', available=True, environment={})
    assert ('-p', 'testmon') in tuple(zip(plan.command, plan.command[1:]))


def test_incremental_mutation_loads_plugin_explicitly(tmp_path):
    from quality.feedback import prepare
    plan = prepare(tmp_path, 'mutation', available=True, environment={})
    assert ('-p', 'gremlins') in tuple(zip(plan.command, plan.command[1:]))
