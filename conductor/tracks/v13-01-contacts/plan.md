# Episode/contact semantics implementation plan

Goal: close the declared v12 follow-on within existing exact-model architecture.
Spec: spec.md and ../../v13-design.md.
Workflow: conductor-implement then conductor-review; keep records.

## Phase/task 1.1: Typed activity and denominator conversion
Files: `src/activity.py`. Tests: `tests/test_v13_activity.py`.
Interface: `ActivitySpec(activity_basis: str="contacts", contacts_per_episode: float=1.0); exposures(forecast: ndarray)->(episodes,contacts)`.
Acceptance: Fixed contacts 37.5 and multiplier2 yields18.75 episodes/37.5 contacts; fixed episodes preserves37.5 and yields75contacts; reject booleans/nonfinite/<1/unknown.

- [x] 1.1.a Write reproducing test(s) for this contract.
- [x] 1.1.b Run `python -m pytest tests/test_v13_activity.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [x] 1.1.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [x] 1.1.d Run scoped tests and dependent regressions; preserve actual green output.
- [x] 1.1.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 1.2: Integrate clinical and workflow exposures
Files: `src/pathways_v6.py; scripts/analyse_v7.py; src/equipment.py`. Tests: `tests/test_v13_activity.py`.
Interface: `compare_v6(...,activity: ActivitySpec|None=None); evaluate_perspectives(...,activity=None); mixed_cash_budget(...,activity=None)`.
Acceptance: At multiplier1 legacy numbers preserved; at fixed episodes2 clinical outcomes unchanged, hours/workflow doubled; at fixed contacts2 outcomes halved but hours unchanged. Ledger conservation and critical/no-effect/failure scenarios remain.

- [x] 1.2.a Write reproducing test(s) for this contract.
- [x] 1.2.b Run `python -m pytest tests/test_v13_activity.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [x] 1.2.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [x] 1.2.d Run scoped tests and dependent regressions; preserve actual green output.
- [x] 1.2.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.
