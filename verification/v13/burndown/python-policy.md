# Python version policy: single bleeding-edge interpreter (2026-10-31)

## Decision

Owner decision (2026-10-31): this is a single-operator health-economics research
project, not a library. It supports **one interpreter: Python 3.15, latest patch on the
3.15 line**. Support for 3.13 and 3.14 is withdrawn; there is no compatibility matrix.

## Precondition checked

Nothing forced an older floor. The resolved lock contains **no package that caps below
3.15** (`uv.lock` per-package `requires-python` scan: none), every pinned dependency
installs and passes on 3.15, and the whole suite ran on 3.15.1 before the change
(1,027 passed).

## Changes

| Item | Before | After |
|---|---|---|
| `pyproject.toml` `requires-python` | `>=3.13,<3.16` | `>=3.15,<3.16` |
| `[tool.ty.environment] python-version` | `3.13` | `3.15` |
| `[tool.basedpyright] pythonVersion` | `3.13` | `3.15` |
| `[tool.ruff] target-version` | `py313` | `py315` |
| `uv.lock` | `requires-python = ">=3.13, <3.16"` | `requires-python = "==3.15.*"` |
| `.github/workflows/ci.yml` assurance job | `python-version: '3.13'` | `python-version: '3.15'` |
| `ci.yml` compatibility matrix job | matrix `['3.14','3.15']` running the quick profile | **removed** |
| `.python-version` | absent | `3.15` (new; local tooling picks the newest 3.15 patch) |
| local `.venv` | 3.15.1 | **3.15.2** (rebuilt with `uv sync --frozen`) |
| `evidence/dependency_targets.json` | `tested_python: 3.13.5` | `tested_python: 3.15` |

Why the matrix job was removed rather than reduced to one entry: it existed to prove
*forward* compatibility on interpreters newer than the assurance job's, and to avoid
duplicating the primary CI. With exactly one supported interpreter it would either
duplicate the gated job or test an unsupported version. The quick profile it ran is a
subset of the `pr`/`full` profiles the assurance job runs, so no coverage is lost. Its
env-install concern is preserved and strengthened by the updated contract test below.

## Contract tests updated with the policy

- `tests/test_v4_config.py::test_ci_pins_the_single_supported_interpreter` (replaces
  `test_primary_ci_is_not_duplicated_in_compatibility_matrix`): asserts the interpreter
  floor declared in `pyproject.toml` equals the `ty` target, the `basedpyright` target
  and the CI pin, that no `matrix:` block remains, and that no `'3.13'`/`'3.14'` string
  survives in the workflow.
- `tests/test_v9_contracts.py::test_ci_exercises_the_optional_extras` (replaces
  `test_compatibility_installs_research_dependencies`): the removed job's real concern was
  that the optional extras are exercised somewhere in CI, so the test now asserts the
  gated `uv sync --frozen` line installs `--group assurance --extra tabular
  --extra research --extra reporting`.

## Consequences surfaced and handled

1. **New target, new findings.** Raising the ruff/type targets to 3.15 surfaced findings
   that the 3.13 target did not: ~17 ruff + ~124 basedpyright + ~15 ty, **all confined to
   the three newest `tests/test_mutation_*.py` files**. They are legitimate test patterns
   (deliberate assignment to frozen dataclasses inside `pytest.raises(FrozenInstanceError)`,
   deliberately invalid inputs) plus genuine sloppiness (redundant `cast`, unused call
   results, missing `Returns:`). Fixed in that scope, with narrow per-line suppressions
   only where the pattern *is* the assertion.
2. **`sources/retrieve_originals.py`** (178 findings) is outside the ruff gate but was
   cleaned anyway so the tree is genuinely tidy; behaviour, URLs, hashes and receipt
   contents were held fixed and checked by AST comparison.

## Known intermittent risk (not papered over)

On 3.15, pytest's own tmp-dir cleanup (`_pytest/pathlib.py::cleanup_numbered_dir`) can
emit an unclosed-scandir `ResourceWarning`, which `filterwarnings = ["error"]` escalates
into intermittent `Error` mutants — and the mutation gate fails on **any** error. Two
consecutive scoped gremlins runs on 3.15 measured **0 errors**, so it is rare, not
deterministic. If it recurs, the fix must address the cause (a pytest-internal bug) or
pin a pytest that does not do it — **not** by relaxing `filterwarnings`, which is a
deliberate project policy.

## Deliberately left unchanged

- `handoff/v13/full_receipt.json` and other sealed receipts still record
  `Python 3.13.5`: those are historical execution evidence and are not rewritten.
- Authored published report prose in `scripts/build_reports_v2.py` mentions the
  3.13/3.14/3.15 matrix and `Python 3.13.5`. That text is part of already-generated
  documents; changing it would alter published output, so it stands as a historical
  statement.
- Closed track plans under `conductor/tracks/` that describe the old matrix are prior
  track history and stay immutable.
