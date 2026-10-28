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
