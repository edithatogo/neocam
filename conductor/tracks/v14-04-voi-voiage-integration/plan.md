# VoI / voiage integration implementation plan

Goal: one VoI camp. `voiage` becomes the maintained engine for value-of-information and
value-of-perspective semantics; `vop_poc_nz` contributes its unique capability to voiage
and then remains an evidence reference; this repository consumes voiage with parity
evidence. No silent change to published numbers.
Spec: spec.md and ../../v14-design.md.
Workflow: conductor-implement then conductor-review. Work in the sibling repository is
governed by that repository's own rules (its AGENTS.md/runbook/CI), which the
reconnaissance dossier records verbatim. One revertable commit per task.

## Phase/task 4.1: Make voiage installable on Python 3.15
Files: `voiage/pyproject.toml` (and every other place the pyarrow cap appears, per the dossier); `uv.lock` there; its CI/docs references.
Interface: voiage declares `pyarrow>=25.0.0,<26`, and pyarrow 25.x publishes **no** cp315 wheels (verified: zero across 25.0.0 and 25.0.1) while pyarrow 26.0.0 does. The cap therefore makes voiage unsatisfiable on this project's only interpreter.
Acceptance: voiage installs and its own suite passes on Python 3.15 with pyarrow 26.x; the cap change is complete (no stale reference left); the change is contributed upstream through voiage's own process, not by overriding the constraint locally.

- [ ] 4.1.a Reproduce: show the unsatisfiable resolution on 3.15 (`uv run --with voiage==2.2.0` fails; pyarrow 25.x has no cp315 wheel).
- [ ] 4.1.b Record the evidence and the exact cap line(s) to change from the dossier.
- [ ] 4.1.c Widen the cap to admit pyarrow 26.x; run voiage's own sync, lint, type and test commands.
- [ ] 4.1.d Confirm a 3.15 install works and its tests pass; preserve the command output.
- [ ] 4.1.e Follow voiage's own contribution process (branch, commit convention, PR), record SHAs and the PR link.

## Phase/task 4.2: Port the vop_poc_nz-only perspective capabilities into voiage
Files: voiage's `methods/perspective.py` (and its exports and tests), following voiage's own layout and conventions.
Interface: voiage already implements contract 1.1.0 (`value_of_perspective`, `perspective_optimal_strategies`, Arrow/Parquet/IPC helpers, Pareto indices). `vop_poc_nz` additionally implements `perspective_acceptability_frontier`, `with_weighted_perspective`, `perspective_mixture_frontier`, `exact_perspective_frontier`, `expected_value_switch_points`, `mcda_feature_records`, `tensor_from_records` and the `NetBenefitTensor` container with its row/segment/switch-point dataclasses.
Acceptance: the ported capabilities live in voiage with tests, preserve contract 1.1.0 semantics and the tie policies (`first`/`split`/`error`), follow voiage's error/typing/serialisation conventions, and resolve any naming collision with voiage's existing helpers. Where the two implementations differ semantically on the overlapping path, the difference is documented rather than averaged away.

- [ ] 4.2.a Write reproducing tests in voiage's style for each capability being ported (they must fail before the port).
- [ ] 4.2.b Preserve the red evidence.
- [ ] 4.2.c Implement the port; reuse voiage's abstractions instead of duplicating them.
- [ ] 4.2.d Run voiage's scoped and full suites plus its gates; preserve green output.
- [ ] 4.2.e Follow voiage's contribution process; record SHAs and the PR link.

## Phase/task 4.3: Make a voiage release that supports Python 3.15
Files: voiage's version/release mechanics (per its dossier).
Interface: a released wheel carrying 4.1 and 4.2, installable on 3.15, so downstream pinning is against a published artefact rather than a branch.
Acceptance: the release exists and installs here; if releases are automated, the workflow run is quoted; if a release is not possible, this task is recorded as blocked with the reason and 4.4 is deferred rather than replaced by a git dependency.

- [ ] 4.3.a Confirm the release mechanics from the dossier and prepare the version bump/changelog entries voiage expects.
- [ ] 4.3.b Execute the release through voiage's own automation.
- [ ] 4.3.c Verify the published wheel installs and imports on Python 3.15 here.
- [ ] 4.3.d Record the exact version, wheel filename and install command in the evidence.
- [ ] 4.3.e Record the outcome (released or blocked with reason) in progress.md.

## Phase/task 4.4: Consume voiage from this model, with parity evidence
Files: `pyproject.toml`; `src/`; `tests/`; `evidence/dependency_targets_v3.json`; the source register if a source record changes.
Interface: voiage becomes a declared dependency of this project's VoI path; the current hand-rolled EVPI/EVoP in `src/statewide.py` and the reimplemented perspective contract in `src/perspectives_v7.py` are compared against voiage on identical inputs.
Acceptance: parity is demonstrated on the retained scenarios, or any difference is disclosed with its magnitude and cause and reviewed before any published figure changes. The dependency is pinned exactly, the lock is regenerated, and the weight of the new (transitive) dependencies — notably pyarrow — is recorded against the design document's "value per dependency" criterion.

- [ ] 4.4.a Add a parity harness that computes the same quantities with both implementations on fixed seeds.
- [ ] 4.4.b Preserve the measured comparison (agree within tolerance, or the exact difference).
- [ ] 4.4.c Wire voiage into the VoI path behind that evidence; pin the version and regenerate the lock.
- [ ] 4.4.d Run the full suite, the parity selection and `quality.checks inputs`; preserve green output.
- [ ] 4.4.e Review, commit and record SHAs in progress.md; disclose any figure change.

## Phase/task 4.5: Retire the duplicate implementations
Files: `src/perspectives_v7.py`; `docs/library-integration.md`; `sources/` references.
Interface: once voiage is authoritative, this repository's reimplementation of the inspected `vop_poc_nz` contract, and any duplicated regret/frontier arithmetic, become redundant.
Acceptance: exactly one implementation of the VoI/perspective semantics remains in the model path; `vop_poc_nz` is recorded as an evidence source (inspected commit, method contract) and **not** a dependency; the change is justified by the parity evidence from 4.4 and preserves every retained output.

- [ ] 4.5.a Identify what becomes redundant and what must stay (evidence provenance stays).
- [ ] 4.5.b Remove the redundant path only after 4.4 parity is recorded.
- [ ] 4.5.c Update `docs/library-integration.md` and the source register stances.
- [ ] 4.5.d Run the full suite, parity and the frozen-input gate; preserve green output.
- [ ] 4.5.e Review, commit and record SHAs in progress.md.
