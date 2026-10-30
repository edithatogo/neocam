# Draft: code-quality gate burn-down plan (not yet a registered track)

Status: draft for review. Promote with `/conductor:newtrack` (or fold into a v14
track) before any execution. Author: assistant, 2026-10-31. No code changed by this
document; it records the measured baseline and a sequenced plan.

## Why

Hosted assurance (ci.yml run 41074874950, commit f8e3e96) executed the full gate set
for the first time: **25 of 31 gates passed, 5 failed, 1 blocked**. The runner
allocation problem is fixed; what remains is pre-existing code-quality debt. Full
acceptance requires every gate to pass, and the project rule is that thresholds are
not lowered — so the debt must be cleared, not waived.

## Measured baseline (2026-10-31, this machine, pinned tools)

### In-scope breakdown (Option B: `quality/`, `src/`, `tests/`, `.agents/`)

Catalogue from a read-only sweep of the four directories:

| Directory | Findings | Auto-fixable | Residual (no `[*]`) | Files to reformat |
|---|---|---|---|---|
| `tests/` | 8,172 | 6,225 | 1,947 | 47 |
| `src/` | 2,039 | 1,497 | 542 | 12 |
| `quality/` | 1,588 | 1,301 | 287 | 14 |
| `.agents/` | 65 | 57 | 8 | 1 |
| `pyproject.toml` | 6 | 6 | 0 | 0 |
| **In scope** | **11,870** | **9,086** | **2,783** | **74** |

Of the 2,783 residual in-scope findings: **2,113 have no automatic fix at all**, and
**~664 are fixable only with `--unsafe-fixes`** (the project sets `unsafe-fixes=false`),
so those are mechanical-but-reviewed rather than manual.

Top residual rules (in-scope): D103 479 · ANN201 432 (unsafe) · ANN001 321 · E702 266 ·
TRY003 158 · E701 150 · EM101 140 (unsafe) · E501 95 · PT011 91 · CPY001 78 · DOC201 71 ·
PLC0415 53 · DOC501 44 · PLR2004 42.

### Delta since B0 (2026-10-31)

- `pyproject.toml`: 6 selector findings fixed (rule codes → names, intent verified).
- `.agents/skills/**` excluded from lint/format as vendored skill payload (rationale in
  `extend-exclude`), replacing a per-file restyle of `audit_evidence.py`.
- Repo-wide `ruff check .` now reports 22,808 fixable remaining / 104 files to reformat.

## Real defects found during the catalogue (fix before style work)

These are logic-adjacent, not style; they should be fixed and independently reviewed
first, each with a reproducing test:

- **RUF069 float equality on the model path** — `src/audit_v7.py:32-35` compares
  reliability values with `!=`/`==` against `.95`, `.5`, etc. Use `math.isclose`
  with an explicit tolerance.
- **TRY004 wrong exception type** — raise `TypeError` (not `ValueError`) for type
  checks: `src/configuration.py:28`, `src/configuration.py:82`, `src/pathways_v6.py:171`,
  `src/statewide.py:86`, `src/strategies.py:48`.
- **B905 `zip()` without `strict=`** — `tests/test_v10_reconciliation.py:13`,
  `tests/test_v9_contracts.py:44`, `tests/test_v9_contracts.py:55`, `tests/test_v9_contracts.py:61`.
- **Unused bindings** — `tests/test_v6_pathways.py:72` (B007 `key`),
  `tests/test_v13_deployment.py:129,146` (RUF059 `p`).
- **Unused imports (F401, auto-fixable)** — `src/portfolios_v7.py:3`,
  `tests/test_quality_gates.py:2`, `tests/test_quality_integration.py:8,11`.
- **Ambiguous names / stray characters** — `tests/test_v12_active_properties.py:20` (E741 `l`),
  `src/sensitivity.py:23` (RUF001 EN DASH in a string, likely meant to be `-`).

## Documented per-file ignores (genuine seams, not suppressions of defects)

- `tests/*.py`: extend the existing ignore to `D103, ANN001, ANN201, ANN202, D100, D104,
  ARG001, ARG005, SLF001, PLC2701` — tests are not a public API; annotating every
  fixture/double is churn with no consumer (the repo already ignores `S101`,
  `magic-value-comparison` there).
- `src/__init__.py`, `tests/__init__.py`: `D104`.
- `S404, S603, S607` (23 findings): assurance tooling that shells to pinned `uv`/tools —
  keep as targeted inline ignores with a justification, not a blanket disable.
- `CPY001` (78): a project-wide policy decision (single copyright header policy) rather
  than 78 scattered edits.


Ruff findings by top-level path:

| Path | Findings | Character |
|---|---|---|
| `scripts/` | 16,548 | historical generation/analysis scripts (v2–v7 builders) |
| `tests/` | 8,172 | substantive rules (docstrings, annotations, PT011, PLR2004) |
| `src/` | 2,039 | model code; highest care |
| `quality/` | 1,588 | harness code |
| `sources/`, `.agents/`, `pyproject.toml` | 179 + 65 + 6 | incl. 6 config-style rules in pyproject |

Rule profile (top): Q000 9,527 · E231 9,232 · E225 2,551 · E226 1,118 · E501 996 ·
E702 846 · D103 567 · ANN001 521 · ANN201 518 · E701 334 · E111 217 · RUF001 208 ·
TRY003 177 · EM101 157. So ~80% is mechanical formatting; the remaining ~5.7k are
documentation/annotation/exception-style judgements.

Worst single files: `scripts/build_workbook.py` 1,695 · `scripts/analyse_v5.py` 1,063 ·
`scripts/build_workbook_v2.py` 1,040 · `scripts/analyse_v7.py` 1,007.

## Scope decision — RESOLVED by the gate commands (owner no longer needed)

The plan originally offered A (fix everything) or B (enforce current-generation code and
exclude `scripts/`). Reading the actual harness settles it: **`scripts/` is inside the
gate scope**, so B is not available without weakening acceptance, which this project
forbids. Evidence:

- `quality/cli.py` — `Gate("ruff_lint", (python, "-m", "ruff", "check", "src", "scripts", "quality", "tests"), ...)`
- `pyproject.toml` `[tool.ty.src].include` and `[tool.basedpyright].include` both list
  `src`, `quality`, `tests` plus nine named scripts (`run_v2.py`, `verify.py`,
  `analyse_v5.py`, `analyse_v6.py`, `analyse_v7.py`, `build_current_report.py`,
  `plot_current.py`, `analyse_refinements.py`, `plot_refinements.py`).

Therefore: `scripts/` is cleared for ruff (Option A), and those nine scripts also feed
the type gates. No gate command, threshold or scope is being changed by this burn-down.
`pyproject.toml`'s own 6 `rule-codes-in-selectors` findings were fixed in B0.

## Phase 4 baseline (measured 2026-10-31, after the ruff work)

- `ty`: **101 diagnostics** — `src` 48, `tests` 28, `scripts` 23, `quality` 22.
- `basedpyright`: **3,813 errors, 0 warnings** — `tests` 2,243, `scripts` 933,
  `quality` 405, `src` 311 (line counts; each error prints its path twice, so read them
  as relative weights).

Both tools run strict (`all`, `failOnWarnings`, no ignores), and a contract test forbids
adding a `basedpyright` ignore block or a `.basedpyright/baseline.json`. Phase 4 therefore
fixes types for real: `tests/` first by volume, then `scripts/`, `quality/`, and `src/`
last, always re-running the parity checks after `src/` edits.

## Invariants (must hold for every batch)

1. `data/`, `outputs/`, `evidence/`, `sources/` bytes are frozen during engineering
   work (`quality.checks inputs` must stay green).
2. Default-result parity: `outputs/v13-primary/results.json` and
   `outputs/v13-refinements/results.json` must be byte-identical before/after (the
   v13 review already established bit-for-bit parity for the kernel).
3. No threshold is lowered; no gate is disabled; no tool is added (`maintaining-lean-ci`
   skill: one authoritative harness, no overlapping scanners).
4. Each batch ends with: scoped gate green, `python -m quality.cli --profile quick`
   green, a receipt under `verification/`, and a single revertable commit.
5. Mutation improvements are real tests for surviving mutants, not score manipulation.

## Phases

- **Phase 0 — freeze and baseline (no code change).** Record `ruff check .`,
  `ruff format --check .`, `ty check`, `basedpyright`, and the gremlins report into
  `verification/v13/burndown/baseline/`. Confirm the quick profile and the two
  parity receipts. Decide A or B. *(B chosen 2026-10-31; B0 config commit landed.)*
  Fix the six real defects listed above, each with a reproducing test, before style work.
- **Phase 1 — mechanical, config first.** ✅ B0 (selectors + vendored-skill exclusion).
  Then `ruff check --fix` + `ruff format` on `quality/`, `src/`, `tests/` in
  directory-sized batches (one revertable commit per batch, `quality/` and `src/`
  before `tests/`), verifying after each batch:
  `ruff check <paths>` leaves only the known residual, `ruff format --check <paths>`
  reports 0, and the mapped scoped tests pass. Expected: removes ~9,086 in-scope
  fixable findings; leaves ~2,783.
  Review risk: the dominant auto-fix is Q000 (quote normalization) — semantics
  preserving, but files asserting verbatim strings should be eyeballed
  (`quality/cli.py`, `quality/hypothesis_properties.py`, `src/statewide.py`,
  `tests/test_quality_integration.py`, `tests/test_contract_adversaries.py`,
  `tests/test_v12_*.py`).
- **Phase 2 — judgement rules in `quality/` and `src/`.** Docstrings (D103/DOC201/
  DOC501), annotations (ANN001/ANN201), exception style (TRY003/EM101/EM102),
  magic values (PLR2004), unused imports (F401), private access (SLF001 — review, do not
  blanket-suppress). Each rule family as its own commit with scoped tests. Consider a
  reviewed per-rule `--unsafe-fixes` pass: ANN201 (~400) + EM101 (~135) is the single
  largest mechanical lever after Phase 1.
- **Phase 3 — judgement rules in `tests/`.** Apply the documented per-file ignores
  first (removes ~1,300 low-value findings), then PT011/PT006 with real `match=`,
  E702/E701 splits, E501 wraps. Tests may be touched freely; the suite must stay green
  and no assertion may be weakened.
- **Phase 4 — type gates.** `ty` first (86 diagnostics, small). Then `basedpyright`:
  reduce the 3.9k partially-unknown errors by adding precise annotations at module
  boundaries, starting with the modules `ty` already flagged; avoid blanket
  `reportUnknown*` disables — if a rule must be relaxed for a genuinely dynamic
  seam, record the reason in `pyproject.toml` with the audit rule name, per
  repository convention.
- **Phase 5 — mutation score 69.78% → ≥90%.** Read the gremlins survivor report,
  group by module, add targeted tests for survivors in `src/` (kernel, statewide,
  strategies, sensitivity first — highest decision value). Re-run `gremlins` +
  `mutation_score` per group. This is the slowest phase; do it last so earlier
  phases are already banked.
- **Phase 6 — flip acceptance.** Confirm all 31 gates green locally
  (`--profile full --evidence-version v13`), then confirm hosted on the same commit.
  Only then may `full_local_assurance`/`release_ready` flags be reconsidered —
  those remain separate governance decisions (publication, clinical review), which
  stay open regardless.

## Rough effort

Phase 1 is mostly tool-driven (hours, review-dominated for `scripts/` in option A).
Phase 2–3 are the bulk of human judgement (~5.7k findings). Phase 4 is bounded
(3.9k errors but repetitive). Phase 5 is open-ended and dominates the schedule.
Hosted CI is now cheap to verify (compat jobs ~25 s; assurance job ~12 min, mostly
gremlins), so each phase can be proven end-to-end.

## Acceptance commands

```bash
uv sync --frozen --group assurance --extra tabular --extra research --extra reporting
uv run --frozen --no-sync ruff check . && uv run --frozen --no-sync ruff format --check .
uv run --frozen --no-sync ty check && uv run --frozen --no-sync basedpyright
uv run --frozen --no-sync python -m quality.cli --profile full --evidence-version v13
```

## Boundaries

Not in scope: new clinical parameters, new dashboards/services/frameworks, model
behaviour changes, dependency upgrades beyond reviewed pins, or publication claims.
The clinical/evidence/publication gates in `conductor/blockers-v13.json` remain
open and are unaffected by this burn-down.
