# Preserve model scope and harden verified inputs

Track `v3-01-input-and-numerical-integrity` | baseline `4be33ea986fc7581634da8b4abd76edbf343bd42` | updated 28 October 2026

## Scope and non-goals
Preserve the existing 27 model parameters and default results. No new clinical features, no new dataframe framework, no public/remote write. Estimated inputs remain estimates. The runbook is the execution authority.

## Completion convention
`complete` means the stated scoped evidence exists. `implemented_verification_blocked` means code/configuration exists but the actual required tool result is missing. `blocked` means the requested prerequisite could not be performed. Packaging is verified by the post-commit delivery receipt; it cannot certify unavailable tooling.

## Task 01 — Reproduce v2 baseline

**Files:** `src/statewide.py`; `tests/test_model.py`; `tests/test_v2.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/baseline.txt` and in this track metadata.

**Acceptance and limits:** 75 baseline tests passed before repairs.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 02 — Freeze assumptions

**Files:** `data/`; `evidence/parameter_register.csv`; `evidence/literature_parameter_map.csv`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `git diff 4be33ea986fc7581634da8b4abd76edbf343bd42 -- data evidence` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/protected_inputs.json` and in this track metadata.

**Acceptance and limits:** All 27 model parameters and nine protected source/data files unchanged; new engineering evidence is separate.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 03 — Reproduce integrity failures

**Files:** `tests/test_v3_regressions.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_v3_regressions.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/red_regressions.txt` and in this track metadata.

**Acceptance and limits:** 15 new tests first failed on v2 behaviour; retain the original failures.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 04 — Repair data and numeric contracts

**Files:** `src/statewide.py`; `tests/test_v3_regressions.py`; `tests/test_contract_adversaries.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_v3_regressions.py tests/test_contract_adversaries.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/green_all.txt` and in this track metadata.

**Acceptance and limits:** Reject malformed and duplicate rows; preserve source year; canonicalise sequences; reject booleans as numbers; stabilise annuities; honour supplied PSA odds ratio.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 05 — Verify economic regression

**Files:** `src/statewide.py`; `verification/v3/default_output_parity.json`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_v2.py tests/test_v3_regressions.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/default_output_parity.json` and in this track metadata.

**Acceptance and limits:** Five deterministic portfolios and pilot/spoke 20,000-draw PSA arrays compared against the original Git commit; rtol 1e-12 and atol 1e-8.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 06 — Audit provenance

**Files:** `quality/contracts.py`; `evidence/`; `tests/test_contract_adversaries.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.checks inputs` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/input_audit.json` and in this track metadata.

**Acceptance and limits:** 27 fields, 15 sources, 7 studies and 46,711 births reconcile; empirical assumptions remain uncertain.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 07 — Commit verified repairs

**Files:** `verification/v3/`; `conductor/decisions-v3.md`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `git log --oneline 4be33ea..HEAD` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/protected_inputs.json` and in this track metadata.

**Acceptance and limits:** Input/model repairs and their reproducing tests committed; no new default clinical/economic parameter.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
