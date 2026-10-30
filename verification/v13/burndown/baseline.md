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
