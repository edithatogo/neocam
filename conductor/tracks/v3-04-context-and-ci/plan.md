# Make single-developer continuation reproducible

Track `v3-04-context-and-ci` | baseline `4be33ea986fc7581634da8b4abd76edbf343bd42` | updated 28 October 2026

## Scope and non-goals
Preserve the existing 27 model parameters and default results. No new clinical features, no new dataframe framework, no public/remote write. Estimated inputs remain estimates. The runbook is the execution authority.

## Completion convention
`complete` means the stated scoped evidence exists. `implemented_verification_blocked` means code/configuration exists but the actual required tool result is missing. `blocked` means the requested prerequisite could not be performed. Packaging is verified by the post-commit delivery receipt; it cannot certify unavailable tooling.

## Task 01 — Unify context entrypoints

**Files:** `AGENTS.md`; `GEMINI.md`; `conductor/runbook.md`; `README.md`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.checks context` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/quick/receipt.json` and in this track metadata.

**Acceptance and limits:** Small entrypoints point to one runbook; read current state plus active track rather than loading historical reports.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 02 — Maintain decision and uncertainty records

**Files:** `conductor/decisions-v3.md`; `conductor/current-state.json`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.checks context` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `conductor/decisions-v3.md` and in this track metadata.

**Acceptance and limits:** Record scope, Polars interpretation, uncertainty, source trust, latest-target versus installed status and all remaining blockers.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 03 — Align CI with local gates

**Files:** `.github/workflows/ci.yml`; `quality/cli.py`

**Status:** `implemented_verification_blocked`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `python -m pytest -q tests/test_toolchain_contracts.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/full/receipt.json` and in this track metadata.

**Acceptance and limits:** Same local gates, frozen environments, read-only permissions, full Git history, SHA-pinned Actions and bounded artifact retention. Hosted execution remains unverified.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 04 — Guard releases

**Files:** `.github/workflows/release-gate.yml`; `scripts/verify.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_assurance_scope.py tests/test_assurance_v3.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/green_all.txt` and in this track metadata.

**Acceptance and limits:** No bypass flag, automatic publication or partial-pass promotion. Release workflow calls the same CI and deliberately does not deploy.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 05 — Validate context and workflow structure

**Files:** `quality/checks.py`; `tests/test_quality_integration.py`; `.github/dependabot.yml`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.checks context` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/quick/receipt.json` and in this track metadata.

**Acceptance and limits:** Context paths/action pins and unsafe bypasses checked; dependency updates are explicit reviewable PRs, not silent auto-merge.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 06 — Attempt submodule materialisation

**Files:** `.gitmodules`; `extensions/conductor`

**Status:** `blocked`

- [ ] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `git submodule update --init --recursive` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/submodule_attempt.txt` and in this track metadata.

**Acceptance and limits:** Current upstream main rechecked and matches the existing pin. The actual checkout attempt failed on github.com DNS; no Conductor CLI run is claimed.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 07 — Record handoff

**Files:** `conductor/tracks.md`; `conductor/current-state.json`; `conductor/runbook.md`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.checks context` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `conductor/current-state.json` and in this track metadata.

**Acceptance and limits:** Handoff identifies the connected dependency-install acceptance task; authoring, economic validity and hosted execution remain separate.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
