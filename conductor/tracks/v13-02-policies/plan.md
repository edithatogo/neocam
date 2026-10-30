# Eligible mixed deployment and shared capacity implementation plan

Goal: close the declared v12 follow-on within existing exact-model architecture.
Spec: spec.md and ../../v13-design.md.
Workflow: conductor-implement then conductor-review; keep records.

## Phase/task 2.1: Strict eligibility and assignment contracts
Files: `src/deployment.py`. Tests: `tests/test_v13_deployment.py`.
Interface: `Eligibility(site,strategy,status,evidence); DeploymentPolicy(name,assignments,conditional); validate_policy(sites,policy,eligibility)`.
Acceptance: Reject omission/duplicate/unknown assignments; conceptual kit disallowed in strict mode; conditional mode must disclose assumptions; reported installed sites only.

- [ ] 2.1.a Write reproducing test(s) for this contract.
- [ ] 2.1.b Run `python -m pytest tests/test_v13_deployment.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 2.1.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 2.1.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 2.1.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 2.2: Paired exact policy accounting
Files: `src/deployment.py`. Tests: `tests/test_v13_deployment.py`.
Interface: `evaluate_policy(sites,policy,eligibility,p,s,assets,*,inputs,structural_draws,activity); policy_cash_budget(...,years=7)`.
Acceptance: Uniform policy matches kernel, mixed retains only compatible owned assets, no repeated clinical cohort, global hub block once even below per-site thresholds; negative transfer benefit signed; original inputs not mutated.

- [ ] 2.2.a Write reproducing test(s) for this contract.
- [ ] 2.2.b Run `python -m pytest tests/test_v13_deployment.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 2.2.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 2.2.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 2.2.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.

## Phase/task 2.3: Explicit scenario catalogue and output driver
Files: `config/refinements.json; scripts/analyse_refinements.py`. Tests: `tests/test_v13_pipeline.py`.
Interface: `main(config_path,refinements_path,output_dir)`.
Acceptance: Generate all4portfolios with paired draws and strict vs conditional sets; 1/1.5/2contacts × fixed contacts/episodes; known pilot retirement/new capital correct; reject existing output and invalid config; export hashes.

- [ ] 2.3.a Write reproducing test(s) for this contract.
- [ ] 2.3.b Run `python -m pytest tests/test_v13_pipeline.py -q`; preserve expected red evidence (or documented configuration-only inspection).
- [ ] 2.3.c Implement minimal existing-stack changes; do not modify scientific input estimates.
- [ ] 2.3.d Run scoped tests and dependent regressions; preserve actual green output.
- [ ] 2.3.e Review diff, apply evidenced fixes, commit and record SHA in progress.md.
