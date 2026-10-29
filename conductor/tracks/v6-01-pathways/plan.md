# Explicit pathways and workload-based hub costing: detailed implementation and acceptance plan

**Constraints:** five complete alternatives; Polars-only DataFrame policy; no new clinical observations; no invented peer review, full texts, lock or hosted-CI results.

**Review focus:** final-transfer endpoint double counting, resource/cash separation, origin/receiving episodes, zero-workload invariance, conditional rescue, evidence access and unsupported certainty.

## Task 1. Restore and test v5 baseline
**Status:** accepted.
**Evidence:** `verification/v6/baseline.txt`.
**Verification:** `python -m pytest -q`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 2. Specify endpoint, fallback, conservation and hospital component contracts
**Status:** accepted.
**Evidence:** `verification/v6/red.txt; tests/test_v6_pathways.py`.
**Verification:** `python -m pytest tests/test_v6_pathways.py -q`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 3. Replace site-count trigger with incremental hours and separate paid capacity
**Status:** accepted.
**Evidence:** `src/pathways_v6.py; tests/test_v6_validation.py`.
**Verification:** `python -m pytest tests/test_v6_validation.py -q`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 4. Implement mutually exclusive immediate/rescue/local pathways in both arms
**Status:** accepted.
**Evidence:** `src/pathways_v6.py; outputs/v6/pathways.csv`.
**Verification:** `python scripts/analyse_v6.py`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 5. Price origin, receiving, final-local and extra pre-rescue care without double count
**Status:** accepted.
**Evidence:** `data/v6/hospital_prototypes.json; tests/test_v6_validation.py`.
**Verification:** `python -m pytest tests/test_v6_validation.py -q`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 6. Reconcile seven-year cash replacement and sunk capital
**Status:** accepted.
**Evidence:** `outputs/v6/budget.csv; replacement tests`.
**Verification:** `python -m pytest tests/test_v6_validation.py -q`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 7. Rerun paired uncertainty, deterministic surfaces and historical-result bridge
**Status:** accepted.
**Evidence:** `outputs/v6/results_v6.json; verification/v6/analysis_run.txt`.
**Verification:** `python scripts/analyse_v6.py`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 8. Keep historical numerical implementation explicitly superseded
**Status:** accepted.
**Evidence:** `src/statewide.py module warning; README.md`.
**Verification:** `python -m quality.checks context`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
