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

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
