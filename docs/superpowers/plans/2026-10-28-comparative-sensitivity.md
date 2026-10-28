# Comparative sensitivity implementation plan

**Goal:** add a reproducible five-strategy decision layer, comprehensive bounded sensitivity
analysis, learning-assisted explanation and a publication-target assessment.
**Architecture:** reuse the existing cohort kernel with shared inputs; optional research
analysis packages outside the NumPy-only runtime; derive every new artifact from saved results.
**Spec:** docs/superpowers/specs/2026-10-28-comparative-sensitivity-design.md
**Global constraints:** preserve protected scientific inputs and v4 defaults; no pandas/xarray;
no unverified clinical equivalence, quotes, deployed CI or activated submodule claims.
**Review focus:** correlated comparisons; negative benefits; reference-cost double counting;
sunk vs new capital; training/test leakage; allocation vs cash; deterministic fractions vs PSA.

- [ ] Task 1 — tests/test_v5_strategies.py: write and run failing tests for five arms,
  telephone zero increments, Panda parity, shared draws, sunk capital and invalid inputs.
- [ ] Task 2 — src/statewide.py/src/strategies.py: expose unchanged parameter sampling,
  implement strategy configuration and exact comparator kernel; run baseline and new tests.
- [ ] Task 3 — tests/test_v5_sensitivity.py/src/sensitivity.py: independent bounded design,
  one-/two-/k-way analyses, ranking/EVPI/regret and checked decision surfaces.
- [ ] Task 4 — scripts/analyse_v5.py: paired PSA for pilot/state and structural alternatives;
  Sobol variance indices, input-only clustering, train/test separation and supervised
  explanation. Exact-model comparison and numerical stability verification.
- [ ] Task 5 — evidence/v5: verify current journal scope, requirements and fees using publishers;
  write submission strategy, evidence boundaries and CHEERS readiness map.
- [ ] Task 6 — scripts/build_artifacts_v5.py and authoring workflow: two-page authentic CHHHS
  plan, supplement, plots/tables, workbook and slides. Render and inspect final outputs.
- [ ] Task 7 — current state and scoped/full receipts; commit, create ZIP/bundle, independently
  restore and run tests. No release success while required gates remain unavailable.
