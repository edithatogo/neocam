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


---

# Current analysis artifacts and reproducible handoff: detailed implementation and acceptance plan

**Constraints:** five complete alternatives; Polars-only DataFrame policy; no new clinical observations; no invented peer review, full texts, lock or hosted-CI results.

**Review focus:** final-transfer endpoint double counting, resource/cash separation, origin/receiving episodes, zero-workload invariance, conditional rescue, evidence access and unsupported certainty.

## Task 1. Migrate assurance, mutation, type and profiler scope to current kernel
**Status:** accepted.
**Evidence:** `tests/test_v6_assurance_scope.py; integration_repair.txt`.
**Verification:** `python -m pytest tests/test_v6_assurance_scope.py tests/test_quality_integration.py -q`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 2. Generate exact-result figures and inspectable tables/workbook
**Status:** accepted within generated/rendered scope.
**Evidence:** `scripts/plot_v6.py; scripts/build_workbook_v6.py`.
**Verification:** `Run plotting and artifact_tool build in the documented Python runtime`.
- [ ] Establish the applicable contract or retrieval requirement.
- [ ] Implement/review within that declared scope.
- [ ] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 3. Regenerate and inspect two-page CHHHS plan, supplement and presentation
**Status:** accepted within generated/rendered scope.
**Evidence:** `scripts/build_documents_v6.py; scripts/build_slides_v6.js`.
**Verification:** `Run builders; render and inspect every page/slide`.
- [ ] Establish the applicable contract or retrieval requirement.
- [ ] Implement/review within that declared scope.
- [ ] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 4. Run complete ordinary suite and scoped coverage
**Status:** local suite accepted; final receipt and restoration logs govern handoff.
**Evidence:** `verification/v6/full/receipt.json`.
**Verification:** `python -m quality.cli --profile full`.
- [ ] Establish the applicable contract or retrieval requirement.
- [ ] Implement/review within that declared scope.
- [ ] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 5. Complete clean locked environment, all external tools and hosted CI
**Status:** blocked.
**Evidence:** `verification/v6/full/receipt.json`.
**Verification:** `Requires real lock/install and hosted execution; not a local-pass claim`.
- [ ] Establish the applicable contract or retrieval requirement.
- [ ] Implement/review within that declared scope.
- [ ] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 6. Commit, bundle and restore the delivered project
**Status:** local suite accepted; final receipt and restoration logs govern handoff.
**Evidence:** `verification/v6/bundle_restore.txt`.
**Verification:** `git bundle verify; clone bundle; python -m pytest -q`.
- [ ] Establish the applicable contract or retrieval requirement.
- [ ] Implement/review within that declared scope.
- [ ] Inspect actual evidence; keep blocked/partial acceptance open.


---

# Evidence verification and transparent validation boundaries: detailed implementation and acceptance plan

**Constraints:** five complete alternatives; Polars-only DataFrame policy; no new clinical observations; no invented peer review, full texts, lock or hosted-CI results.

**Review focus:** final-transfer endpoint double counting, resource/cash separation, origin/receiving episodes, zero-workload invariance, conditional rescue, evidence access and unsupported certainty.

## Task 1. Retrieve critical full articles through PubMed, publisher and repository routes
**Status:** partial.
**Evidence:** `evidence/v6/full_text_verification.csv`.
**Verification:** `Inspect documented retrieval level for each source`.
- [ ] Establish the applicable contract or retrieval requirement.
- [ ] Implement/review within that declared scope.
- [ ] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 2. Keep poster, abstract and complete article evidence distinct
**Status:** accepted.
**Evidence:** `evidence/v6/retrieval_status.json`.
**Verification:** `Inspect source register and limitations`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 3. Document selection, overlapping cohorts and clinical endpoint uncertainty
**Status:** accepted.
**Evidence:** `evidence/v6/full_text_verification.csv`.
**Verification:** `Inspect model-use and applicability fields`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 4. Compare a separately expressed scalar calculation and hand-worked case
**Status:** accepted-author-only.
**Evidence:** `tests/test_v6_validation.py; verification/v6/independent_arithmetic.txt`.
**Verification:** `python -m pytest tests/test_v6_validation.py -q`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 5. Run clinical/economic/evidence/software subagent panel
**Status:** blocked.
**Evidence:** `docs/validation/v6/panel_status.json; four reviewer briefs`.
**Verification:** `Requires an actual independent agent execution facility; not available here`.
- [ ] Establish the applicable contract or retrieval requirement.
- [ ] Implement/review within that declared scope.
- [ ] Inspect actual evidence; keep blocked/partial acceptance open.

## Task 6. Map ISPOR/AdViSHE/TECH-VER/CHEERS domains without certification claims
**Status:** accepted-author-assessment.
**Evidence:** `docs/validation/v6/standards_assessment.csv`.
**Verification:** `Review mapping, gaps and pending independent validation`.
- [x] Establish the applicable contract or retrieval requirement.
- [x] Implement/review within that declared scope.
- [x] Inspect actual evidence; keep blocked/partial acceptance open.
