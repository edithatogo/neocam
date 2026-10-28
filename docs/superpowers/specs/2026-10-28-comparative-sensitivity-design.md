# Five-strategy neonatal consultation evaluation

## Intent and authority
User explicitly requested continued implementation, five alternatives, one-/two-/k-way DSA,
PSA, unsupervised then supervised analysis, publication options and updated repo/artifacts.
These instructions authorise a new comparative analysis layer; they supersede the v4
engineering-only restriction. The nine protected v2/v3 source/input files remain unchanged.

## Approaches
1. Replace the cohort model with a new simulation: rejected; no evidence need and poor auditability.
2. Add a thin five-strategy layer over the tested common-input kernel: selected by implementer.
3. Rank devices using machine learning alone: rejected; no clinical device-effect data and no
justification for replacing the small exact model with a surrogate.

## Decision model
Telephone is the common incremental zero comparator, not cost-free clinical care. Four video
configurations: mobile teleconference ($45k), installed Panda ($10k), fixed ceiling/wall PTZ
($47k), complete tablet-OBSBOT kit ($4.5k unquoted assumption; $7.5k alternative). Same video
clinical effect, reliability and workflow in the reference analysis. This tests costs under
assumed parity; it does not establish equivalence. OBSBOT is a component in existing setups;
the fifth strategy is a distinct complete configuration, not a $349 camera.

Use paired shared uncertainty across strategies and sites. Maintain critical-case transfers.
Compare greenfield investment, retained installed Panda, and sunk existing generic equipment.
Account for full budget vs attributable resource cost; shared-use fractions are not cash savings.
Keep a conditional five-choice set and a set excluding unvalidated tablet adoption.

## Sensitivity and interpretation
Full one-way curves, pre-specified two-way grids, a bounded deterministic 12-D Sobol design,
selected k-way grids, and a separate prior-based paired PSA. Deterministic design frequencies
are NOT probabilities. Add variance-based Sobol sensitivity on independent design coordinates.
Cluster standardised INPUTS without outcome labels. Train supervised surrogate(s) and a shallow
rule tree on a separate development sample; evaluate on an independently scrambled held-out
design. Report balanced accuracy, confusion, regret and held-out permutation importance.
Do not equate importance with value of research; report cost-only EVPI/expected regret separately.
Exact model results remain authoritative; no causal or empirical effectiveness claims from ML.

## Boundaries
No new patient data, no verified current QEP, no manufactured quotes or clinically established
device superiority, no new lifetime utility calibration. Latest target != installed version.
No new remote publication, GitHub push or global skill installation. Optional scientific
analysis dependencies use NumPy arrays, no pandas/xarray DataFrame engine. Tests and exact
v4 result parity precede delivery. All requested prior tool gates remain mandatory if unavailable.
