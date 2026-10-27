# Verify refinements without reissuing unsupported economic claims

Track `v3-05-final-verification-and-packaging` | baseline `4be33ea986fc7581634da8b4abd76edbf343bd42` | updated 28 October 2026

## Scope and non-goals
Preserve the existing 27 model parameters and default results. No new clinical features, no new dataframe framework, no public/remote write. Estimated inputs remain estimates. The runbook is the execution authority.

## Completion convention
`complete` means the stated scoped evidence exists. `implemented_verification_blocked` means code/configuration exists but the actual required tool result is missing. `blocked` means the requested prerequisite could not be performed. Packaging is verified by the post-commit delivery receipt; it cannot certify unavailable tooling.

## Task 01 — Run full local tests

**Files:** `tests/`; `quality/`; `src/`

**Status:** `implemented_verification_blocked`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `python -m quality.cli --profile full` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/full/receipt.json` and in this track metadata.

**Acceptance and limits:** Ordinary tests, coverage and input/context gates run locally; the overall full profile remains unsuccessful until requested external checks run.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 02 — Inspect result invariance

**Files:** `data/`; `evidence/`; `verification/v3/default_output_parity.json`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.checks inputs` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/default_output_parity.json` and in this track metadata.

**Acceptance and limits:** Protected input hashes and numerical baseline parity checked after repairs; no new economic artifacts or parameters.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 03 — Review all changes

**Files:** `verification/v3/review.md`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `git diff --check` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/review.md` and in this track metadata.

**Acceptance and limits:** Author self-review found and repaired unsafe URL/digest categorisation, missing resolver pin and host-dependent test assumptions. No independent review claimed.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 04 — Complete track statuses

**Files:** `conductor/tracks/v3-*/`; `conductor/current-state.json`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.checks context` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `conductor/tracks.md` and in this track metadata.

**Acceptance and limits:** Every task carries exact files/command/acceptance evidence and separates implementation from external acceptance.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 05 — Package reproducible history

**Files:** `Panda_Vision_project_v3.zip`; `Panda_Vision_project_v3.bundle`; `verification/v3/delivery.json`

**Status:** `delivery_verification_recorded_separately`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `git bundle verify /mnt/data/Panda_Vision_project_v3.bundle` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/delivery.json` and in this track metadata.

**Acceptance and limits:** Deliver the committed source, readout, gate logs and full Git history; validate ZIP CRC, bundle and SHA256 manifest. No remote push.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.
