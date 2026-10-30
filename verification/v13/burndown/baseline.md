# Burn-down baseline and Phase 1 result (2026-10-31)

Scope: Option B — enforce on current-generation code (`quality/`, `src/`, `tests/`,
`.agents/skills` excluded as vendored, `scripts/` frozen historical).
Tooling: pinned ruff 0.17.3 via `uv run --frozen --no-sync`.
All figures are `ruff check <dir>` findings; format column is `ruff format --check`.

## Baseline (before Phase 1)

| Directory | Findings | Auto-fixable | Residual | Files to reformat |
|---|---|---|---|---|
| `tests/` | 8,172 | 6,225 | 1,947 | 47 |
| `src/` | 2,039 | 1,497 | 542 | 12 |
| `quality/` | 1,588 | 1,301 | 287 | 14 |
| `.agents/` | 65 | 57 | 8 | 1 |
| `pyproject.toml` | 6 | 6 | 0 | 0 |
| **In scope** | **11,870** | **9,086** | **2,783** | **74** |

Repo-wide (including frozen `scripts/` and `sources/`): 28,597 findings, 22,872
fixable, 105 files to reformat.

## Phase 1 applied (mechanical: `ruff check --fix` then `ruff format`, no `--unsafe-fixes`)

| Directory | Before | After mechanical | Format after | Scoped tests |
|---|---|---|---|---|
| `quality/` | 1,588 | 252 | 0 to reformat (16 files) | 60 passed, 1 pre-existing contract failure (see below) |
| `src/` | 2,039 | 483 | 0 to reformat (12 files) | 155 passed; parity selection 15 passed; `quality.checks inputs` errors: [] |
| `tests/` | 8,172 | 1,524 | 0 to reformat (49 files) | 135 passed; 676 tests collected cleanly |

Q000 (quote normalization) was audited for semantic risk: an AST comparison of
string-literal value multisets before/after showed all `quality/` files identical —
zero literal values changed. `src/` changes were confined to rules Q000, E231, E226,
E225, E252, E227, E228, E306, E302, I001, F401 plus format reflow; default-output
parity tests pass. `tests/` had no assertion or `pytest.raises` match string changed;
the only security-rule delta was removal of a genuinely unused `subprocess` import.

## Config policy landed with Phase 1

- `pyproject.toml` selectors now use canonical rule names (satisfies
  `rule-codes-in-selectors`); the contract test was updated to assert the same
  intent in name form — global ignores remain exactly the two formatter conflicts.
- `extend-exclude` now covers `.agents/skills` (vendored skill payloads).
- Documented per-file ignores for `tests/*.py` (not a public API): undocumented
  functions/modules/packages, missing argument and return annotations, unused
  arguments, private member access, private imports, implicit namespace package.
- `missing-copyright-notice` disabled via per-file ignore: this repository has no
  LICENSE file and deliberately ships no per-file copyright headers, so asserting
  ownership per file would be inaccurate.

## Contract failure observed and resolved

`tests/test_toolchain_contracts.py::test_ruff_all_preview_no_unsafe_fixes` asserted
`lint.ignore ⊆ {COM812, ISC001}` (codes). It failed after the selector rename and was
updated to assert the equal set in canonical name form. The guard's intent
(only documented formatter conflicts are globally disabled) is unchanged — importantly
it also forbids adding anything to global `lint.ignore`, which is why all new
suppressions are per-file or per-line.

## Still open after Phase 1 (in scope)

| Directory | Residual after config policy | Remaining character |
|---|---|---|
| `src/` | ~470 | exception style (TRY003/EM101/EM102), docstrings, magic values, arg counts, + 2 real defects (RUF069 float equality, TRY004 exception types) |
| `tests/` | ~251 | PT011 (`match=`), PT006, lazy imports, float comparisons in assertions |
| `quality/` | ~237 | T201 CLI output, exception style, docstrings, complexity |

Note: the assurance runner's `python-style` commit hook runs ruff on changed files, so
every touched file must reach zero findings before it can be committed — which is why
Phase 2 is executed per directory rather than deferred.

## Phase 2 results — `quality/` and `src/` complete

| Directory | Residual after Phase 1 + config policy | After Phase 2 | Format | Verification |
|---|---|---|---|---|
| `quality/` | 237 | **0** | clean (16 files) | 678-test full suite passed; `checks context` exit 0; workflow hook exit 0 |
| `src/` | 470 | **0** | clean (13 files) | 165 scoped passed; 22 parity passed; `quality.checks inputs` errors: []; quick profile green |

### Two genuine defects fixed in `src/` (with failing-first tests)

1. **RUF069 — float equality on the model path** (`src/audit_v7.py`, `sample_v7`).
   Reliability parameters were compared to reference defaults with exact `!=` against
   `0.95 / 0.5 / 0.05`. Now compared with `math.isclose(..., rel_tol=_REFERENCE_REL_TOL)`
   (`1e-9`) against `Parameters()` / `PathwaySpec()` defaults. Tests:
   `tests/test_v7_sampling_health.py::test_reference_draws_are_compared_with_explicit_tolerance`
   and `::test_non_reference_reliability_is_still_redrawn`. Evidence recorded by the
   agent: a `0.95 + 1e-12` input keeps the reference draw under the new comparison and
   was wrongly redrawn under the old one, so the test fails on the previous code.

2. **TRY004 — wrong exception type for type errors.** `ValueError` → `TypeError` in
   `configuration.strict_json` (root, owned_assets), `pathways_v6.compare_v6` (activity),
   `statewide.Parameters` (case_mix sequence), `strategies._validate_overrides`
   (non-numeric override). Bad-VALUE paths still raise `ValueError`; the corresponding
   suites retain their `ValueError` cases, so the distinction is enforced both ways.
   Tests added/adjusted in `test_v13_activity.py`, `test_v12_configuration.py`,
   `test_v5_strategies.py`, `test_contract_adversaries.py`.

### Mechanism summary

- `quality/`: 46 per-line justified ignores (26 `print` for CLI receipts, 13
  subprocess/path rules for pinned-tool execution, deferred/`sys.path` imports, plus
  three single cases). Real fixes elsewhere: hoisted exception messages, docstrings,
  annotations, named constants, `PERF401`, `RUF005`, `FBT003`, and helper extraction
  resolving `C901`/`PLR0912`/`PLR0915`/`PLW0717`. A `PLR6201` conversion exposed a
  set-literal membership on an unhashable value, fixed as a real defect.
- `src/`: 20 per-line justified ignores, all on published model/budgeting/kernel APIs
  where argument counts or boolean flags are deliberate (`PLR0913`/`PLR0917`/`PLR0914`/
  `FBT001`/`FBT002`/`C901`). Real fixes elsewhere: 128 hoisted raise messages, docstrings,
  annotations with `TYPE_CHECKING`, 33 magic values → named constants, one EN DASH fix.
- Numeric integrity: an AST literal sweep against a pre-change copy confirmed the only
  numeric-literal movement is the four `audit_v7` reference values into dataclass
  defaults plus the new `_REFERENCE_REL_TOL`; every other removed literal is replaced by
  an equal-valued named constant. No formula, default, seed, array order or comparison
  semantics changed. Parity tests (22) and the frozen-input gate agree.

## Still open

`tests/` residual (~251) is in progress: `PT011` with real `match=` patterns, `PT006`,
`PLW1514` encodings, `RUF069` assertions via `pytest.approx`, and lazy imports. Then the
type gates (`ty`, `basedpyright`) and the mutation-score phase remain.

