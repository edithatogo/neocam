# v14 design authority — engineering rigour, acceptance integrity and ecosystem integration

Date: 2026-10-31. Owner decisions supersede earlier drafts in this file.
Status: implementation begun; external acceptance remains a separate gate.

This document is the design authority for the v14 tracks. It records the measured
dependency audit, the "foot in two camps" findings with options and tradeoffs, and the
decisions taken, so later work does not have to re-derive them.

## Owner decisions already taken

1. **One interpreter.** Python 3.15 only (`requires-python >=3.15,<3.16`); no 3.13/3.14
   support. Implemented and verified (`verification/v13/burndown/python-policy.md`).
2. **Maximal strictness.** ruff `select = ["ALL"]` + preview; ty `all = "error"` plus
   `--error-on-warning`; basedpyright `all` + experimental features + blanket
   `# type: ignore` banned + ignore auditing; pytest strict markers/config,
   warnings-as-errors and `xfail_strict`. Implemented.
3. **Bleeding-edge CI/security.** SHA-pinned actions, harden-runner, CodeQL,
   dependency-review, OpenSSF Scorecard, SLSA-style evidence attestation, hardened
   Renovate, `SECURITY.md`, `.gitignore` leak vectors. Implemented.
4. **reportlab is incorporated, not removed.** It must do real work in the document
   pipeline (track `v14-01`, task 1.1) rather than sit declared-but-unused.

## Dependency audit (measured 2026-10-31, installed versions)

| Dependency | Actual use | Verdict |
|---|---|---|
| numpy 2.5.4 | 46 files; `default_rng`/`Generator`, `numpy.typing.NDArray`, no deprecated aliases | at top of scope |
| polars 2.1.0 | independent reconciliation probe (rows/sum/nulls/duplicates) + gate | deliberate second engine |
| python-docx 1.2.0 | 7 files; private `_element`/`_p` OOXML handles (11 justified ignores) | private API is unavoidable today |
| python-pptx 1.0.2 | 1 file | fine |
| reportlab 5.1.0 | **zero imports before this track** | to be incorporated (task 1.1) |
| matplotlib 3.11.2 | 7 files; `matplotlib.typing.ColorType` available but unused; ~7 suppressions from untyped `**kwargs` | fixable gap (task 1.4) |
| scipy 1.18.1 | only `scripts/analyse_v5.py`; Sobol `random_base2` + `optimization=` available | historical analysis only |
| scikit-learn 1.9.1 | same legacy script; `FrozenEstimator`, `set_config` unused | historical analysis only |
| hypothesis 6.170.14 | one file; `max_examples=100, deadline=None, derandomize=True`; no `target()`/`event()` | gap: `deadline=None` disables a check; `derandomize=True` stops exploring new examples |
| coverage 7.17.0 | branch, fail-under 90 (+95 core) | `COVERAGE_CORE=sysmon` available, unused |
| pip-audit 2.10.1 | `--local` json + cyclonedx SBOM | `--vulnerability-service=osv` available, unused |
| uv 0.13.6 | `lock --check`, `sync --frozen`, `run --no-sync` | `uv pip check`, `uv export`, `uv python pin` unused |
| pytest-gremlins 1.13.1 | 5 operators, `max_pardons=0`, 2 workers, acceptance cache off | batching/sharding available for speed |
| ty, basedpyright, ruff, scalene, testmon, xdist, prek, zizmor | at their maximum strictness settings | fine |

## "Foot in two camps" decisions

### D1 — reportlab (owner decision: incorporate)
- Task 1.1: reportlab must produce a real artefact with a test and a receipt, and must
  not duplicate the matplotlib PDF path. Intended use: a paginated PDF document (the
  decision memo / plan) where ReportLab's text flow and page furniture are genuinely
  better than a figure-based PDF.
- Contingency: if the artefact duplicates an existing DOCX with no added value, the
  track records that finding and the dependency returns to the audit list rather than
  being silently kept.

### D2 — ty + basedpyright (recommendation: keep both)
- Options: (a) keep both; (b) basedpyright only; (c) ty only; (d) ty in hooks,
  basedpyright in the gate.
- Rationale: they found different defects on this codebase — basedpyright found breadth
  (`reportAny`, partially-unknown types), ty found `invalid-assignment`,
  `redundant-cast`, `unsound-assignment`. That is independent signal, not duplication.
- Tradeoff: ~86 suppression comments and two gate runtimes.
- Decision: (a) keep both; the division of labour is recorded here. Contingency (d) if
  cost outweighs value.

### D3 — scipy + scikit-learn scope
- Finding: they are used only by the historical `scripts/analyse_v5.py`; the model
  (`src/sensitivity.py`) is numpy-only.
- Decision: keep, documented as historical-analysis tooling; the runbook states the
  model itself needs numpy only.

### D4 — performance tooling
- Decision: do **not** add `pytest-benchmark`; scalene (gate) plus the bespoke
  benchmark module remain the single performance camp. Contingency: adopt
  pytest-benchmark only if the bespoke module is retired in the same change.

### D5 — secret scanning depth
- Decision: do **not** add trufflehog. gitleaks (commit + push) and GitHub push
  protection already cover pattern matching and server-side blocking; trufflehog's
  unique value (verifying live credentials) does not apply to this repository.

### Deliberate non-violations (do not "fix" later)
polars reconciles the source table independently of the model's numpy path; actionlint
(syntax) and zizmor (security audits) are complementary; hypothesis (property) and
gremlins (mutation) are different; testmon and xdist are routed per mode because they
conflict; coverage is used directly (no pytest-cov).

## Track map

| Track | Scope |
|---|---|
| `v14-01-engineering-rigour` | reportlab incorporation, testing depth, static-analysis depth, custom-validation replacement spike, experimental feature trials |
| `v14-02-acceptance-integrity` | source-register and artifact-manifest governance (including the re-seal-last rule), full-profile green, hosted CI evidence |
| `v14-03-ecosystem-integration` | sibling-repository incorporation: provenance, privacy patterns, citation verification, CI alignment |

## Boundary

No clinical parameter, model behaviour, published number or output path changes in v14.
The clinical/evidence/publication gates in `conductor/blockers-v13.json` remain open and
are unaffected. Frameworks are not added to the model: any dependency replacing custom
code must be justified per-agreement, measured, and confined to the harness (task 1.5).
