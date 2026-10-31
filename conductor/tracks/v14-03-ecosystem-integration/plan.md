# Ecosystem integration implementation plan

Goal: replace one-off reinvention with the owner's existing, more advanced sibling
repositories wherever that is the honest choice, and record the decision for each.
Spec: spec.md and ../../v14-design.md.
Workflow: conductor-implement then conductor-review; keep records. One revertable commit
per task. The owner must choose the incorporation form per repository before a task
starts; nothing is merged from a sibling without that decision.

## Phase/task 3.1: Inventory and per-repository incorporation decision
Files: `conductor/v14-design.md`; `docs/library-integration.md`; `sources/source_register.csv`.
Interface: extend the existing external-reference document into a full inventory covering every sibling that is materially relevant, each with a checked commit, the form of incorporation, and what is explicitly *not* claimed.
Acceptance: each entry names the repository, the pinned or checked commit, the form (submodule / documented reference / dependency / CI reuse / not relevant), and the reason; existing entries for `mchs`, `microcosting_healthworkforce`, `voiage` and `vop_poc_nz` are preserved and extended, not rewritten.

- [ ] 3.1.a Enumerate candidate siblings and classify relevance (direct, adjacent, unrelated).
- [ ] 3.1.b For each direct sibling, record a checked commit and the proposed form with rationale.
- [ ] 3.1.c Implement the documentation change only; no dependency or submodule added without the owner's form decision.
- [ ] 3.1.d Verify links resolve and the context gate passes; preserve the output.
- [ ] 3.1.e Review, commit and record SHA in progress.md.

## Phase/task 3.2: Privacy automation borrowed from `careops-rims`
Files: `.github/workflows/`; `quality/`; `tests/`.
Interface: a privacy check that fails on personal identifiers in tracked evidence and generated artefacts, modelled on the sibling's `privacy.yml`, without flagging the published aggregate facility table.
Acceptance: the check passes on the current tree and fails on a synthetic identifier fixture; exemptions are explicit and documented; it does not weaken secret scanning.

- [ ] 3.2.a Add a synthetic identifier fixture and show the check failing on it.
- [ ] 3.2.b Implement the minimal workflow/check; wire it into the required gate set.
- [ ] 3.2.c Confirm the real tree passes and gitleaks/push protection remain in force.
- [ ] 3.2.d Run the full suite and workflow hooks; preserve green output.
- [ ] 3.2.e Review, commit and record SHA in progress.md.

## Phase/task 3.3: CI pattern alignment with `template-solo-data`
Files: `.github/workflows/`; `renovate.json`; docs.
Interface: compare this repository's CI/Renovate/OIDC pattern against the solo-maintainer template and adopt only the parts that are strictly better (for example OIDC-based coverage upload instead of a token).
Acceptance: each adopted pattern is justified with the difference it makes; nothing is adopted merely for consistency; the repository's stricter bespoke gates are preserved.

- [ ] 3.3.a Diff the pattern inventory (workflows, bot config, OIDC) and list candidate adoptions.
- [ ] 3.3.b Adopt one candidate at a time, with the before/after recorded.
- [ ] 3.3.c Reject the rest with a one-line reason each.
- [ ] 3.3.d Verify workflow gates (actionlint/zizmor) and the context check.
- [ ] 3.3.e Review, commit and record SHA in progress.md.

## Phase/task 3.4: Canonical VoI alignment with `voiage` and `vop_poc_nz` (gated)
Files: `src/perspectives_v7.py`, `src/strategies.py`, `src/statewide.py`; `docs/library-integration.md`.
Interface: this repository reimplements the inspected `vop_poc_nz` contract and computes cost-only EVPI; `voiage` is the owner's VoI engine and has a canonical sync with `vop_poc_nz`.
Acceptance: **not started** until the owner confirms decision utility is credible. If it proceeds, it is a model track with its own parity suite: results may legitimately change, and the change must be separately reviewed and disclosed, never folded into engineering work.

- [ ] 3.4.a Obtain the owner's decision on decision-utility credibility.
- [ ] 3.4.b If approved, pin the sibling engine at a checked commit and write a parity suite.
- [ ] 3.4.c Record any result change explicitly, with the parity evidence.
- [ ] 3.4.d Do not merge into an engineering commit; open a model track instead.
- [ ] 3.4.e Record the outcome (proceed or deferred) in progress.md.
