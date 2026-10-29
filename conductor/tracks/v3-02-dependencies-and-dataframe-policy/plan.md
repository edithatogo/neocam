# Refresh direct releases without inflating runtime

Track `v3-02-dependencies-and-dataframe-policy` | baseline `4be33ea986fc7581634da8b4abd76edbf343bd42` | updated 28 October 2026

## Scope and non-goals
Preserve the existing 27 model parameters and default results. No new clinical features, no new dataframe framework, no public/remote write. Estimated inputs remain estimates. The runbook is the execution authority.

## Completion convention
`complete` means the stated scoped evidence exists. `implemented_verification_blocked` means code/configuration exists but the actual required tool result is missing. `blocked` means the requested prerequisite could not be performed. Packaging is verified by the post-commit delivery receipt; it cannot certify unavailable tooling.

## Task 01 — Verify latest release targets

**Files:** `evidence/dependency_targets_v3.json`; `quality/native-tools.json`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_toolchain_contracts.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `evidence/dependency_targets_v3.json` and in this track metadata.

**Acceptance and limits:** Primary registry/release records checked; latest located release targets are not installed-version claims.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 02 — Declare minimal dependency groups

**Files:** `pyproject.toml`; `conductor/tech-stack.md`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_toolchain_contracts.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/green_toolchain.txt` and in this track metadata.

**Acceptance and limits:** One numerical dependency, a Polars tabular extra, and explicit test/assurance groups. Resolver pin is enforced too.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 03 — Reject forbidden dependencies

**Files:** `quality/contracts.py`; `quality/polars_probe.py`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `python -m pytest -q tests/test_assurance_v3.py tests/test_contract_adversaries.py` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/green_all.txt` and in this track metadata.

**Acceptance and limits:** AST import checks and resolved-graph policy reject pandas/xarray; real Polars reconciliation is a separate unavailable gate.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 04 — Create reproducible lock workflow

**Files:** `pyproject.toml`; `.github/workflows/ci.yml`; `quality/contracts.py`

**Status:** `implemented_verification_blocked`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `python -m quality.checks lock` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/lock_resolution_attempt.txt` and in this track metadata.

**Acceptance and limits:** Frozen lock workflow implemented; missing/empty/unhashed/banned-package graphs are rejected. Actual transitive lock is absent.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 05 — Resolve and install target stack

**Files:** `uv.lock`; `.venv/`; `.tools/bin/`

**Status:** `blocked`

- [ ] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `uv lock --upgrade && uv sync --frozen --group assurance --extra tabular` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/lock_resolution_attempt.txt` and in this track metadata.

**Acceptance and limits:** Actual package resolution attempted and failed on PyPI DNS. Native downloads similarly failed. No lock or installed environment fabricated.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 06 — Verify compatibility

**Files:** `quality/checks.py`; `.github/workflows/ci.yml`

**Status:** `blocked`

- [ ] Implement the scoped change described below, without modifying the protected model assumptions.

- [ ] Execute `uv run --frozen --group assurance --extra tabular python -m quality.cli --profile full` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/full/receipt.json` and in this track metadata.

**Acceptance and limits:** Full installed compatibility and Python 3.13–3.15 hosted matrix still require a connected run.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## Task 07 — Commit manifest and policy

**Files:** `pyproject.toml`; `evidence/dependency_targets_v3.json`; `conductor/runbook.md`

**Status:** `complete`

- [x] Implement the scoped change described below, without modifying the protected model assumptions.

- [x] Execute `git diff --check` and examine the actual exit status and output; do not substitute a configuration inspection for tool execution.

- [x] Preserve the outcome or precise blocker at `verification/v3/review.md` and in this track metadata.

**Acceptance and limits:** Manifest/policy and a reproducible connection-enabled handoff are implemented; no silent fallback to older releases.

**Repair rule:** For a newly discovered behaviour defect, add the reproducing test first, retain its failing output, apply the smallest repair, and rerun the complete ordinary suite. Never lower thresholds or add blanket suppressions to obtain a green status.

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
