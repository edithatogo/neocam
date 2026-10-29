# Neocam / Panda Vision — draft recovery branch

Private working destination for the Queensland neonatal teleconsultation economic evaluation.

## Import is PARTIAL

[Draft PR #3](https://github.com/edithatogo/neocam/pull/3) now contains all nine original model modules in `src/`, all nine original model input files in `data/`, the regional analysis driver, selected assurance modules and regression tests, dependency/CI configuration, and reconciled developer context.

The `src` Git subtree is `cc0bbb89ece22b08f498937595d3f5c10846b0fd` and the `data` subtree is `2530ae6e70fb2ff9c5d517014b85378764e5085e`. Both match the complete recovered local project exactly.

**The remaining tests, supporting scripts, evidence files, original track files, binary artifacts and complete historical ancestry have NOT all been imported. This branch is not a complete distribution and is not ready to merge.** Missing references are recorded as recovery gaps, not silently replaced with invented files.

## Current model and correction

The active model uses `src/pathways_v6.py` with regional/perspective adapters. `src/statewide.py` and `src/panda_model.py` retain historical models for reproducibility; do not use their superseded hub/rescue logic for current decisions.

No primary financial parameters or numerical model modules changed during v9. The secondary age-11 utility scenario generator in `scripts/analyse_v7.py` now explicitly discounts from year 11. Historical v7 utility tables and figures are not newly corrected merely because the generator is fixed.

## Reconciled work and actual assurance

- [All 19 historical tracks, checked in order](conductor/reconciliation-v9.md).
- [Current task ledger](conductor/tracks/v9-reconciliation/plan.md).
- [Authoritative runbook](conductor/runbook.md).
- [Local-versus-remote verification status](handoff/v9/status.json).

The complete LOCAL project passes 507 ordinary tests. Its full run enumerated 30 mandatory gates: seven passed, 22 blocked, one failed. The failed gate correctly rejects an absent genuine `uv.lock`; required external tools and Gitleaks have not passed. The local receipt does not certify this partial remote branch.

A real [hosted CI run](https://github.com/edithatogo/neocam/actions/runs/40882632395) failed before a runner was allocated, with zero executed steps reported. Its underlying account/platform cause is not established. No successful hosted model run is claimed.

The Conductor submodule gitlink is preserved, but the populated checkout is not certified. No force push, main-branch merge, public release or repository-visibility change has been performed.

## Scientific and privacy boundary

This is a preliminary model, not clinical validation or procurement approval. Four critical full texts, original public-source archival gaps and independent clinical/economic validation remain open. No patient-level records were added. Restricted corporate assets in the private local handoff must not be redistributed publicly without permission.

Complete migration remains tracked in [issue #2](https://github.com/edithatogo/neocam/issues/2).
