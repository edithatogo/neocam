# Integrated reproduction, review and private delivery implementation plan

Goal: close the declared v12 follow-on within existing exact-model architecture.
Spec: spec.md and ../../v13-design.md.
Workflow: conductor-implement then conductor-review; keep records.

## Phase/task 4.1: Active invariants, artifact manifest and supplement
Files: `quality/hypothesis_properties.py; quality/artifacts.py; scripts/plot_refinements.py`. Tests: `tests/test_v13_pipeline.py`.
Interface: `Extend current property definitions and manifest source coverage; seal/verify new outputs`.
Acceptance: Add active contact/policy invariants without removing legacy tests. Fulltext, tool installation, physical approval and independent review still gates; charts display units and conditional labels.

- [x] 4.1.a Write reproducing test(s) for this contract.
- [x] 4.1.b Run `python -m pytest tests/test_v13_pipeline.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [x] 4.1.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [x] 4.1.d Run scoped tests and dependent regressions; preserve actual green output.
- [x] 4.1.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 4.2: Conductor review, fix and reconcile
Files: `verification/v13/review.md; conductor/tracks.md`. Tests: `tests/test_v13_review.py`.
Interface: `Review changed files against all4specs; record findings/fixes and exact commits`.
Acceptance: Execute scoped/full suite; resolve important reproducible defects before final; retain review as author not independent. Reconcile affected v12 followups only.

- [x] 4.2.a Write reproducing test(s) for this contract.
- [x] 4.2.b Run `python -m pytest tests/test_v13_review.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [x] 4.2.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [x] 4.2.d Run scoped tests and dependent regressions; preserve actual green output.
- [x] 4.2.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 4.3: Frozen assurance and verified delivery
Files: `handoff/v13/`, `verification/v13/`; no new clinical inputs or dependencies.
Acceptance: execute every gate, never waive an unavailable tool, and separate complete local history from a partial remote checkout.

- [x] 4.3.a Inspect mandatory-gate and receipt tests; no new feature or manufactured failing test is required for executing the existing release process.
- [x] 4.3.b Execute `python -m pytest -q` and `python -m quality.cli --profile full --evidence-version v13`; retain completed and interrupted receipts separately. Completed pre-final-context run:676 tests,8 gates passed,22 blocked,1 failed. Final snapshot is rerun after this documentation repair.
- [x] 4.3.c Attempt real lock/native/submodule/Git push commands; retain failure logs in `conductor/blockers-v13.json`. Read-only connector discovery and DNS failures remain external blockers.
- [~] 4.3.d Freeze source/context and execute the same full command, compare both fingerprints and all log hashes, then write final evidence only under `verification/` and `handoff/`. The executable driver does not depend on this checkbox changing afterwards; the final status is recorded in `handoff/v13/status.json`.
- [~] 4.3.e Build the complete Git bundle and a small update patch; restore the bundle, run `git fsck --full` and `python -m pytest -q`; attach exact results under `handoff/v13/` without modifying the tested source snapshot.
- [ ] 4.3.f On an authorised connected write surface, push a review branch with an expected-head check, read back all transferred objects and update PR #3. No force push, main merge or visibility change. Do not describe the existing PR as containing v13 until this succeeds.

Final local execution and restoration results supersede the pre-final run only when exact evidence exists. Full external acceptance and remote delivery remain open even when local packaging succeeds.
