# Use one explicit gate runner for local development and CI

Track `v3-03-solo-assurance-harness` | baseline `4be33ea986fc7581634da8b4abd76edbf343bd42` | updated 28 October 2026

## Scope and non-goals
Preserve the existing 27 model parameters and default results. No new clinical features, no new dataframe framework, no public/remote write. Estimated inputs remain estimates. The runbook is the execution authority.

## Completion convention
`complete` means the stated scoped evidence exists. `implemented_verification_blocked` means code/configuration exists but the actual required tool result is missing. `blocked` means the requested prerequisite could not be performed. Packaging is verified by the post-commit delivery receipt; it cannot certify unavailable tooling.

## Task 01 — Test failure semantics

**Files:** `quality/assurance.py`; `tests/test_assurance_v3.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_assurance_v3.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/red_exit69.txt` and in this track metadata.

**Acceptance and limits:** Distinct failed/blocked semantics; subprocess failures cannot hide as missing tools; timeouts fail; designated prerequisites alone may use exit 69.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 02 — Configure Ruff comprehensively

**Files:** `pyproject.toml`; `tests/test_toolchain_contracts.py`

**Status:** `implemented_verification_blocked`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `python -m ruff check src scripts quality tests && python -m ruff format --check src scripts quality tests` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/full/receipt.json` and in this track metadata.

**Acceptance and limits:** ALL + preview, formatter/docstring formatting, safe fixes only, two formatter-conflict exemptions and test-local assertions/literals. Real diagnostics not available.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 03 — Configure two type checkers

**Files:** `pyproject.toml`; `quality/cli.py`

**Status:** `implemented_verification_blocked`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `python -m ty check && python -m basedpyright` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/full/receipt.json` and in this track metadata.

**Acceptance and limits:** ty all-errors and basedpyright all-rules; no broad ignores or generated baseline. First real run may require annotation/refactor repairs.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 04 — Add generative and mutation checks

**Files:** `quality/hypothesis_properties.py`; `quality/checks.py`; `pyproject.toml`

**Status:** `implemented_verification_blocked`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `python -m pytest tests quality/hypothesis_properties.py --gremlins --gremlin-workers=2 --gremlin-clear-cache --gremlin-report=json --strict-pardons` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/full/receipt.json` and in this track metadata.

**Acceptance and limits:** Eight generative properties and five mutation operators configured; independent JSON score gate rejects zero mutants, inconsistent counts, errors, timeouts and pardons. No mutation score claimed.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 05 — Add profiling and security/prose checks

**Files:** `quality/profile_workload.py`; `quality/bootstrap.py`; `.gitleaks.toml`; `.vale.ini`; `.vale/styles/Panda/`

**Status:** `implemented_verification_blocked`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `python -m quality.cli --profile full` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/native_install_attempt.txt` and in this track metadata.

**Acceptance and limits:** Fixed existing PSA CPU/memory workload; pinned native binary hashes and versions; history/tree secret scans; local prose rules; audit/SBOM. Integrity failures tested, tool executions blocked.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 06 — Run a fail-closed unified harness

**Files:** `quality/cli.py`; `scripts/verify.py`; `tests/test_quality_integration.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m quality.cli --profile full` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/full/receipt.json` and in this track metadata.

**Acceptance and limits:** One local/CI entrypoint; quick is never full; all gates attempted; missing prerequisites return nonzero rather than a fabricated release pass.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 07 — Verify receipts

**Files:** `quality/assurance.py`; `tests/test_assurance_v3.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_assurance_v3.py tests/test_quality_integration.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/green_all.txt` and in this track metadata.

**Acceptance and limits:** Commands, exits, durations, source/input hashes and log digests bound; stale, duplicate, extra-failed or tampered receipts rejected. These are audit records, not cryptographic attestations.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 08 — Commit harness evidence

**Files:** `verification/v3/`; `conductor/current-state.json`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `git log --oneline 4be33ea..HEAD` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/review.md` and in this track metadata.

**Acceptance and limits:** Actual local gate receipts and blockers committed. Author self-review is distinguished from independent and hosted assurance.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.
