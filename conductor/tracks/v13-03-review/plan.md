# Clinical plausibility packet and unresolved evidence implementation plan

Goal: close the declared v12 follow-on within existing exact-model architecture.
Spec: spec.md and ../../v13-design.md.
Workflow: conductor-implement then conductor-review; keep records.

## Phase/task 3.1: Fail-closed reviewer records
Files: `quality/clinical_review.py`. Tests: `tests/test_v13_review.py`.
Interface: `review_errors(packet:dict,expected_snapshot:str)->list[str]`.
Acceptance: Pending/blank/simulated records cannot establish independent validation; stale snapshot/unknown role/unresolved material finding fails. Real reviewers not invented.

- [ ] 3.1.a Write reproducing test(s) for this contract.
- [ ] 3.1.b Run `python -m pytest tests/test_v13_review.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 3.1.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 3.1.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 3.1.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 3.2: Review packet, source and acceptance blocker registry
Files: `scripts/analyse_refinements.py; conductor/blockers-v13.json`. Tests: `tests/test_v13_pipeline.py`.
Interface: `Write predictive rows, review_packet.json and blocker registry with required evidence/actions`.
Acceptance: Prior-predictive population conservation, finite costs and count bounds execute; clinical appropriateness remains human question. Network failures and fulltext access limits explicit.

- [ ] 3.2.a Write reproducing test(s) for this contract.
- [ ] 3.2.b Run `python -m pytest tests/test_v13_pipeline.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 3.2.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 3.2.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 3.2.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.
