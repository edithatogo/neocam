# V7 implementation and acceptance record

**Goal:** Answer regional investment and perspective questions with traceable estimates, not fabricated certainty.
**Architecture:** Reuse the exact v6 pathway kernel. Thin NumPy adapters handle portfolios, signed ledgers and fixed-decision regret. CSV is sufficient; no new framework or DataFrame engine.
**Constraints:** shared systematic draws; no new empirical effect; private corporate sources; no independent-agent claim; raw originals distinguished from extracts; no remote writes.

## Task 1: Regional roster and missingness

**Files:** src/portfolios_v7.py; outputs/v7/regional_roster.csv

**Evidence/check:** `tests/test_v7_regional.py`

**Status:** Implemented; current local capability approval remains open.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 2: Explicit workload overrides

**Files:** src/pathways_v6.py

**Evidence/check:** `tests/test_v7_regional.py`

**Status:** Implemented; default historical arithmetic preserved.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 3: Government, family and provider ledgers

**Files:** src/perspectives_v7.py; scripts/analyse_v7.py

**Evidence/check:** `tests/test_v7_perspectives.py`

**Status:** Implemented; payer/receiver/subsidy shares remain scenarios.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 4: Fixed-choice directional VoP and ties

**Files:** src/perspectives_v7.py; sources/extracts/vop_method_contract.md

**Evidence/check:** `tests/test_v7_perspectives.py`

**Status:** Implemented; inspected upstream contract, not imported whole package.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 5: Parameter/distribution audit and beta repair

**Files:** src/audit_v7.py; evidence/v7/parameter_audit.csv

**Evidence/check:** `tests/test_v7_sampling_health.py`

**Status:** Implemented; 49 fields include retired inputs; no local model fit.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 6: Health thresholds and utility bridge

**Files:** src/audit_v7.py; sources/extracts/EPICure2_utility_extract.csv

**Evidence/check:** `tests/test_v7_sampling_health.py`

**Status:** Implemented; causal QALY/DALY effects and complete burden data remain open.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 7: Receiving catchment and mixed-incumbent repair

**Files:** scripts/analyse_v7.py

**Evidence/check:** `tests/test_v7_review_repairs.py`

**Status:** Implemented after reproducing errors; only three pilot installations are treated as retained.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 8: Source archive and safe retrieval

**Files:** sources; quality/source_archive.py

**Evidence/check:** `tests/test_v7_source_archive.py; tests/test_v7_review_repairs.py`

**Status:** Stored-byte validation implemented; original public downloads failed and remain incomplete.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 9: Simulated multidisciplinary review

**Files:** docs/validation/v7/simulated_panel.md

**Evidence/check:** `Manual scope/claim review against code and outputs`

**Status:** Completed author role passes only. Independent review remains open.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 10: Rerun exact scenario/perspective analyses

**Files:** scripts/analyse_v7.py; outputs/v7

**Evidence/check:** `python scripts/analyse_v7.py`

**Status:** Executed 44×20,000 paired structures, 1,452 allocation rows, 48 thresholds and 54 utility bridges.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 11: Plots, tables and branded artifacts

**Files:** scripts/build_*_v7.*; scripts/plot_v7.py

**Evidence/check:** `Render/inspect every document page and slide; reconcile workbook formulas`

**Status:** Generated; final render and artifact receipts retained at handoff.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.

## Task 12: CI/security, commit and restoration

**Files:** quality; verification/v7; .github/workflows/ci.yml

**Evidence/check:** `python -m quality.cli --profile full; git bundle verify; restored ordinary tests`

**Status:** Ordinary tests/integrity checks executable. Gitleaks and external full-stack/lock/hosted acceptance remain blocked or failed, not waived.

- [x] Inspect and document the controlling assumption or failure.
- [x] Implement the bounded change or transparently record the retrieval/acceptance limit.
- [x] Retain actual outputs and tests available in this environment.
- [ ] External clinical/connected acceptance where identified above; not implied by implementation.


## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
