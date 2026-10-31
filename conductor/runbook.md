# Neocam v14: engineering rigour and acceptance integrity

Design authority: `conductor/v14-design.md`. Track register: `conductor/tracks.md`. This runbook remains the authoritative workflow.

## Numerical scope
One interpreter: Python 3.15 (`requires-python >=3.15,<3.16`). The model is numpy-only. scipy and scikit-learn exist solely for the historical `scripts/analyse_v5.py`; polars exists solely for the independent source-table reconciliation. No new clinical parameter, learned model, orchestrator or output path.

## Strictness and quality settings
ruff `select = ["ALL"]` with preview rules; ty `all = "error"` plus `--error-on-warning`; basedpyright `all` with experimental features, blanket `# type: ignore` banned, ignore comments must name their rule; pytest strict markers/config, warnings-as-errors and `xfail_strict`. No global lint ignore beyond the two documented formatter conflicts, no type-checker baseline file, no lowered threshold. The mutation floor is 90% and currently measures 99.52% (1,244/1,250).

## Reproduction
```
python -m quality.cli --profile quick
uv run --frozen --group assurance --extra tabular --extra research --extra reporting \
  python -m quality.cli --profile full --evidence-version v13
```
Ordering rule — the artifact re-seal must be the **last** mutation before acceptance:
```
python -m quality.artifacts seal --output outputs/v13-primary
python -m quality.artifacts seal --output outputs/v13-refinements
python -m quality.artifacts verify
# then immediately: full profile, and nothing else edits source afterwards
```
Both `sources/manifest.json` (which pins the retrieval tool's own bytes) and the artifact manifests (which pin every calculation input) are invalidated by any later source edit. A mid-wave seal is therefore always stale. Use new output paths for reruns; never overwrite retained analyses. `OAI_IS_JUPYTER_KERNEL=false` avoids irrelevant host initialisation; `PYTEST_DISABLE_PLUGIN_AUTOLOAD=1` is ordinary-suite control only, never a substitute for a required gate.

## Boundaries
Read `blockers-v13.json` and `validation-v12.md`. Claim a lock, external tool, gitleaks scan, populated submodule, independent validation or hosted run only when its evidence actually passes. No new patient records, clinical estimates or fabricated observations. Review forms bind source and configuration; their pending records are not clinical approval. Append execution records only under `verification/` and `handoff/`.

## Delivery
The repository is **public** (owner decision 2026-10-31) with GitHub secret scanning and push protection enabled, on top of gitleaks at commit and push time. Actions are SHA-pinned with least-privilege permissions, and CodeQL, dependency-review, Scorecard and build-provenance attestation run alongside the assurance gate. `main` is untouched; PR #3 remains a draft; the `conductor/neocam-v13-decision-refinements` branch shares no merge-base with `main`, so merging is a governance decision, not a routine merge. Never force-push `main`, never claim an unexecuted hosted run, and never publish corporate or licensed assets.
