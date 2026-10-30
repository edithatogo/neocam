# Integrated reproduction, review and private delivery implementation plan

Goal: close the declared v12 follow-on within existing exact-model architecture.
Spec: spec.md and ../../v13-design.md.
Workflow: conductor-implement then conductor-review; keep records.

## Phase/task 4.1: Active invariants, artifact manifest and supplement
Files: `quality/hypothesis_properties.py; quality/artifacts.py; scripts/plot_refinements.py`. Tests: `tests/test_v13_pipeline.py`.
Interface: `Extend current property definitions and manifest source coverage; seal/verify new outputs`.
Acceptance: Add active contact/policy invariants without removing legacy tests. Fulltext, tool installation, physical approval and independent review still gates; charts display units and conditional labels.

- [ ] 4.1.a Write reproducing test(s) for this contract.
- [ ] 4.1.b Run `python -m pytest tests/test_v13_pipeline.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 4.1.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 4.1.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 4.1.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 4.2: Conductor review, fix and reconcile
Files: `verification/v13/review.md; conductor/tracks.md`. Tests: `tests/test_v13_review.py`.
Interface: `Review changed files against all4specs; record findings/fixes and exact commits`.
Acceptance: Execute scoped/full suite; resolve important reproducible defects before final; retain review as author not independent. Reconcile affected v12 followups only.

- [ ] 4.2.a Write reproducing test(s) for this contract.
- [ ] 4.2.b Run `python -m pytest tests/test_v13_review.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 4.2.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 4.2.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 4.2.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 4.3: Frozen assurance and verified PR update
Files: `handoff/v13; verification/v13`. Tests: `full suite and quality.cli`.
Interface: `Run all gates on frozen source, preserve exact receipts; lease remote update and read back tree/blob hashes`.
Acceptance: Never fabricate lock or green missing tools; no force/main merge; verify private destination, current head and migration inventory. Supply complete local history and scoped patch if migration still blocked.

- [ ] 4.3.a Write reproducing test(s) for this contract.
- [ ] 4.3.b Run `python -m pytest full suite and quality.cli -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 4.3.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 4.3.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 4.3.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.
