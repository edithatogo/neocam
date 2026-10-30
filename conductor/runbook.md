# Neocam v13: bounded episode/contact and deployment refinements
Resolve context through index.md and current-state.json. Read v13-design.md and only the active track. Use repository conductor-implement/conductor-review adapters; source pins are in skill-provenance-v13.json.

## Numerical scope
Existing declared inputs flow through src.configuration.load_configuration. data/v6/spec.json is a reference snapshot, not a live configuration input. config/refinements.json supplies labelled sensitivity settings, not locally estimated contact rates or approval records. Episodes govern clinical outcomes; contacts govern incremental workload. Uniform six-perspective reference remains separate from mixed-policy health-system/bounded-family results.

## Reproduction
python -m scripts.reproduce --output outputs/v13-primary
python -m scripts.analyse_refinements --output outputs/v13-refinements
python -m scripts.plot_refinements --output outputs/v13-refinements
python -m quality.artifacts seal --output outputs/v13-primary
python -m quality.artifacts seal --output outputs/v13-refinements
python -m quality.artifacts verify
python -m quality.cli --profile full --evidence-version v13
Use new output paths for reruns; never overwrite retained analyses. config/assurance.json selects all current outputs. Review forms bind source and configuration; their pending records are not clinical approval. Code and context must be frozen before final assurance; append actual execution records only under verification/handoff.

## Boundaries
Read blockers-v13.json and validation-v12.md. No genuine lock, required external tools, Gitleaks, populated submodule or independent validation is claimed unless evidence actually passes. OAI_IS_JUPYTER_KERNEL=false avoids irrelevant host initialisation; PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 is only ordinary-suite control, not a substitute for required extension gates. Polars only for DataFrames; NumPy/stdlib permitted. No new patient records, clinical estimates, runtime orchestrators or learned decision model.

## Private delivery
User authorised private edithatogo/neocam updates. Existing PR #3 remains draft. This session's GitHub tool surface is read-only; actual CLI push was DNS-blocked. Do not imply remote changes, force-push, merge main or change visibility. Full source/history and actual external review remain distinct acceptance tasks. The complete local bundle and incremental patch are current delivery; preserve historical source/artifact rights.
