# v5 author review

- Five-arm prices describe complete systems; reference equivalence is a hypothesis, not a clinical finding.
- Default Panda draws agree with original v4 exactly within numerical tolerances.
- Corrected an output-manifest self-hash defect using RED/GREEN tests; the self-referential digest is excluded.
- Renamed ambiguous locally_validated metadata to documented_local_service; service documentation is not effect validation.
- Extended mutation/type scopes and changed current receipt paths so the old v4 receipts are not overwritten.
- One analysis rerun was interrupted by the execution environment. Instrumented retry completed in 30.75 seconds; no algorithm change or unverifiable speed claim. Initial regression surrogate had unacceptable decision fidelity; classifier choice used a separate selection sample, then a fresh holdout. Initial diagnostic holdout is retired.
- Input clusters weak/unstable; all retained. No discovered clinical regimes claimed.
- Exact-cost EVPI is annual, prior-dependent and objective-specific. Permutation importance is not EVPPI.
- Source years, complete installed costs, QEP, retrieval marginals and hardware feasibility retain their documented uncertainty.
- Final review is author self-review, not independent clinical/economic review or a fresh subagent review.

## Final full-suite scope and bounded lock check
The first full run exposed five stale fixture/receipt paths in existing integration tests after versioned evidence moved from v4 to v5. They now exercise the current path, with the explicit current-version regression still independent. The 371 passing tests did not excuse those five failures. A new regression first failed for online lock verification; the acceptance command now uses `uv lock --check --offline` with a 30-second bound. Resolving/upgrading the lock remains a separate connected maintenance operation. Missing or invalid locks still fail; no dependency check was bypassed.

## Figure review
The five-way grid has four winning alternatives, with Panda never preferred on that particular fixed-prototype slice. Its over-broad title was corrected to “Preferred configuration across the five-way grid”. Other grids and the independent 12-dimensional design permit all five options. Design counts remain explicitly distinct from PSA probabilities.

## Research-extra verification
The new optional SciPy/scikit-learn analysis group initially lacked a path through the inherited installed-version gate and frozen CI install command. Reproducing tests failed first. Full assurance now installs the research extra and checks every declared optional extra; receipts include the actually installed SciPy/scikit-learn versions. This remains configured rather than hosted-tested because genuine dependency resolution is blocked. The exact runtime kernel remains NumPy-only.
