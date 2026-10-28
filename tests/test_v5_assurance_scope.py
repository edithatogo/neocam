"""New scientific modules and receipts must enter the existing assurance scope."""
from pathlib import Path
import tomllib
from quality.cli import gates_for_profile
ROOT=Path(__file__).resolve().parents[1]


def test_current_receipts_do_not_overwrite_previous_version():
    commands=[' '.join(g.command) for g in gates_for_profile('full')]
    assert not any('verification/v4/' in c for c in commands)
    assert any('verification/v5/scalene.json' in c for c in commands)


def test_new_numerical_modules_are_mutation_targets():
    cfg=tomllib.loads((ROOT/'pyproject.toml').read_text())
    assert {'src/strategies.py','src/sensitivity.py'} <= set(cfg['tool']['pytest-gremlins']['paths'])


def test_analysis_script_is_in_both_typecheck_scopes():
    cfg=tomllib.loads((ROOT/'pyproject.toml').read_text())
    assert 'scripts/analyse_v5.py' in cfg['tool']['ty']['src']['include']
    assert 'scripts/analyse_v5.py' in cfg['tool']['basedpyright']['include']


def test_lock_validation_does_not_try_network_resolution():
    gate=next(g for g in gates_for_profile('full') if g.name=='dependency_consistency')
    assert '--offline' in gate.command
