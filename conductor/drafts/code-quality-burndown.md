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

| Gate | Measured result | Notes |
|---|---|---|
| `ruff_lint` | **28,597 findings** | 22,872 auto-fixable (`[*]`), 5,727 need judgement |
| `ruff_format` | **105 files would be reformatted** (126 already formatted) | mechanical |
| `ty` | **86 diagnostics** | |
| `basedpyright` | **3,923 errors, 0 warnings** | strict; partially-unknown types dominate |
| `mutation_score` | **69.78%** vs 90% required | gremlins killed/survivors |
| `locked_versions` | fixed 2026-10-31 (`--extra reporting` synced); local exit 0 | not part of this burn-down |

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

## Scope decision required first (owner)

Two defensible targets; the plan assumes A unless the owner chooses B.

- **A. Fix everything, including historical scripts.** Largest diff, touches
  versioned scripts whose outputs are already frozen and published in `outputs/`.
  Reformatting cannot change numerics, but it does churn historical files.
- **B. Enforce on current-generation code (`src/`, `quality/`, `tests/`, `.agents/`),
  formally exclude `scripts/` as historical, documented in `pyproject.toml` and the
  runbook.** ~11.9k findings, keeps frozen historical artifacts untouched.

Either way, `pyproject.toml`'s own 6 `rule-codes-in-selectors` findings should be
fixed (harmless, config-only).

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
  parity receipts. Decide A or B.
- **Phase 1 — mechanical, config first.** Fix `pyproject.toml` selector findings.
  Then `ruff check --fix` + `ruff format` on the smallest-risk scope first
  (`quality/`, `src/`), verify parity + tests, commit. Then `tests/`, then (A only)
  `scripts/` in directory-sized batches (one file family per commit where a family
  exceeds ~500 findings, e.g. one `build_*` script per commit).
  Expected: removes ~22.8k findings; leaves ~5.7k.
- **Phase 2 — judgement rules in `quality/` and `src/`.** Docstrings (D103/DOC201/
  DOC501), annotations (ANN001/ANN201), exception style (TRY003/EM101), magic values
  (PLR2004), unused imports (F401), private access (SLF001 — review, do not blanket-
  suppress). Each rule family as its own commit with scoped tests.
- **Phase 3 — judgement rules in `tests/`.** PT011 (add `match=`), PLR2004 (named
  constants), parameterise-name types, annotations. Tests may be touched freely; the
  suite must stay green and no assertion may be weakened.
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
