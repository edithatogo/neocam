# Neocam v12 — consistent execution and exact evidence

Read current-state.json, v12-design.md and only the active track needed for the task. The reusable lean-CI skill remains in .agents/skills/maintaining-lean-ci.

## Authoritative analytical path
config/reference.json -> src.configuration.load_configuration -> scripts.analyse_v7 -> outputs/v12.
Declared values, source hashes and run controls are exported in resolved_inputs.json. Live pathways are config/pathways.json. data/v6/spec.json is a reference snapshot, not a live configuration input.
The site equipment estate is shared by retained-capital calculations and current cash budgets. Do not use the legacy global-incumbent budget helper to describe a mixed regional estate.

## Reproduction
python -m scripts.reproduce --output outputs/a-new-run --office
python -m quality.artifacts verify --output outputs/a-new-run
python -m quality.cli --profile full --evidence-version v12
Do not overwrite historical analyses. Rendering and report dependencies are separate from the exact numerical kernel. Current CSVs/JSON, memo, slides and figures derive from the same declared run. Historical v7 Office files are not the current release.

## Freeze before acceptance
Finalise all code, config and Conductor files, regenerate affected artifacts, seal the artifact manifest, and commit those sources. Then execute final assurance. Do not modify fingerprinted files after that run; append final status/logs only under verification or handoff. Bind generated outputs consumed by tests separately from input fingerprints. Source/test/config changes require relevant reruns; artifact-only changes require refreshed artifact verification and affected tests.
A completed run is not a successful run. Preserve blocked/failed gates and exact logs. No fabricated lock, suppressed missing tool, hosted pass or independent-review claim.

## Environment
OAI_IS_JUPYTER_KERNEL=false disables irrelevant notebook-host initialisation in this environment. PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 is used by the available-host ordinary suite; explicit dedicated property/mutation gates remain required. The observed environment is not the pinned project environment.

## Scope control and release
No new clinical effect assumptions, ML surrogate or CI framework. Record new refinements as bounded decision questions. Read validation-v12.md for contacts per infant, mixed deployment, independent clinical/economic review, source gaps and privacy. Public publication requires separate explicit approval and a file-level licence/confidentiality review; Gitleaks is not that review.
Keep existing private PR #3; expected-head writes only, no force push/main merge. Full remote file/history migration remains open unless verified. Final actual execution evidence is verification/v12/full/receipt.json; do not put predicted counts in this runbook.
