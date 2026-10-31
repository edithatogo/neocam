"""Execute the real doctest examples carried by the model and harness packages.

``--doctest-modules`` is deliberately not used: it imports every module under the
given directories, including ones that must not be imported during collection.
The explicit inventory below keeps that decision visible instead of relying on a
blanket ignore, and the companion test proves the mechanism is not vacuous.
"""

from __future__ import annotations

import doctest
import importlib
from pathlib import Path

import pytest

# Modules that may carry executable examples and import without network access,
# pinned native downloads or profiling side effects.
EXECUTED = (
    "quality.assurance",
    "quality.contracts",
    "src.activity",
    "src.configuration",
    "src.deployment",
    "src.equipment",
    "src.pathways_v6",
    "src.statewide",
    "src.strategies",
)

# Required to stay unimported here, with the reason:
#   quality.bootstrap: downloads pinned native tools from the network
#   quality.polars_probe: needs the optional polars extra
#   quality.profile_workload: exists solely to be profiled by scalene
#   quality.hypothesis_properties: registers the panda_ci profile at import time
NOT_IMPORTED = (
    "quality.bootstrap",
    "quality.polars_probe",
    "quality.profile_workload",
    "quality.hypothesis_properties",
)

# Five examples currently exist (three in forbidden_imports, two in
# forbidden_packages); the floor fails loudly if they are quietly dropped.
MINIMUM_EXAMPLES = 4


@pytest.mark.parametrize("module_name", EXECUTED)
def test_importable_modules_run_their_examples(module_name: str) -> None:
    """Every example in an imported module docstring must actually pass."""
    results = doctest.testmod(importlib.import_module(module_name), report=True)
    assert results.failed == 0


def test_example_inventory_is_not_vacuous() -> None:
    """The doctest mechanism must keep real examples in it, not an empty pass."""
    finder = doctest.DocTestFinder()
    found = sum(
        len(test.examples) for module_name in EXECUTED for test in finder.find(importlib.import_module(module_name))
    )
    assert found >= MINIMUM_EXAMPLES


def test_excluded_modules_are_named_with_a_reason_in_this_file() -> None:
    """Modules that must not be imported are documented, never silently skipped."""
    source = Path(__file__).read_text(encoding="utf-8")
    for module_name in NOT_IMPORTED:
        assert module_name not in EXECUTED
        assert module_name in source
