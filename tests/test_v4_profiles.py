"""Prevent duplicate test work and accidental promotion of partial assurance."""

from quality.cli import gates_for_profile


def test_full_suite_runs_once_under_coverage():
    commands = [g.command for g in gates_for_profile("full")]
    ordinary = [
        c for c in commands if "pytest" in c and "--gremlins" not in c and "quality/hypothesis_properties.py" not in c
    ]
    assert len(ordinary) == 1
    assert "coverage" in ordinary[0]


def test_pr_has_covered_tests_without_expensive_mutation_or_profiler():
    gates = gates_for_profile("pr")
    assert "coverage" in {g.name for g in gates}
    assert not {"gremlins", "scalene"} & {g.name for g in gates}


def test_full_retains_fresh_mutation_and_all_required_checks():
    gates = {g.name: g for g in gates_for_profile("full")}
    assert "--gremlin-clear-cache" in gates["gremlins"].command
    assert {
        "ruff_lint",
        "ty",
        "basedpyright",
        "hypothesis",
        "mutation_score",
        "scalene",
        "gitleaks_history",
        "gitleaks_tree",
        "vale",
        "dependency_lock",
        "actionlint",
        "zizmor",
        "prek_config",
        "polars_consistency",
    } <= gates.keys()


def test_profile_gates_are_unique():
    for profile in ("quick", "pr", "full"):
        gates = gates_for_profile(profile)
        assert len(gates) == len({g.name for g in gates})
