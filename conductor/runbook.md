# Panda Vision v7: authoritative runbook

Read current-state.json, tracks/v7-perspectives/spec.md and its plan.md. For assurance work read .agents/skills/maintaining-lean-ci/SKILL.md. Historical runbooks are references, not current commands.

## Decision and model
Active base: src/pathways_v6.py. Regional adapter: scripts/analyse_v7.py; src/portfolios_v7.py; src/perspectives_v7.py; src/audit_v7.py. No new clinical effectiveness is inferred. Forecast consultations are assumed to represent distinct clinical episodes; repeated calls remain a denominator limitation. Retain only the three known Panda installations when modelling regional expansion. CHHHS receiving resources are restricted to the modelled regional catchment.

Six evaluative views reconcile resource costs and transfers. Government allocation scenarios are not actual entitlement/cash models. Provider CHHHS is nested, not additive. Value of perspective selects fixed expected-value strategies; it is not per-draw EVPI. Ties and ties' regret bounds remain explicit. The societal extension is bounded, not comprehensive. No reference QALY/DALY gain is claimed. The utility bridge begins at age 11 and discounts to birth; continuation and affected fractions are hypothetical. See evidence/v7/method_assumptions.csv for 30 additional existing numerical/structural choices.

## Reproduce
Set OPENBLAS_NUM_THREADS=1 and OMP_NUM_THREADS=1 for repeatable resource use.
- python scripts/analyse_v7.py
- python scripts/plot_v7.py
- python scripts/build_workbook_v7.py (artifact_tool authoring environment)
- python scripts/build_documents_v7.py
- node scripts/build_slides_v7.js
- python scripts/audit_v7.py
- python scripts/archive_sources_v7.py
- python -m quality.source_archive

Run ordinary tests: PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -m pytest -q on the shared host. Autoload caused hangs here; the responsible third-party plugin is not established. This does not certify required external pytest extensions. The isolated, frozen environment and dedicated external-tool gates remain authoritative for full acceptance.

Run full harness: python -m quality.cli --profile full. Current evidence goes to verification/v7/full. One covered ordinary execution is reused. Unavailable tools, missing real uv.lock and an unpopulated submodule are not successes. Do not silently disable dedicated plugins or lower thresholds. Research dependencies are optional; numerical v7 adds no pandas/xarray or new runtime package.

## Sources and safety
sources/manifest.json binds actual files. Public original-source completeness is false. sources/retrieve_originals.py --fetch is an opt-in allowlisted bounded download; it is not an automatic background process. Transcriptions are not original PDFs/XLSX. Keep corporate originals and the ELC pricing excerpt private. Do not redistribute the full ELC pack. No patient-level records were added. A bounded pattern scan is not Gitleaks or a full-history/binary security audit.

## Review and release
The user authorised simulated roles. docs/validation/v7/simulated_panel.md is same-author self-review; never describe it as independent agents or clinician sign-off. Independent validation, four critical full texts, full original-source acquisition, local capability/routing/costs, current QEP, connected lock/toolchain/Gitleaks/hosted CI and actual Conductor checkout remain open. No push, submission or deployment is authorised by this local handoff.

Commit, bundle and restore; run ordinary tests from the restored tree and inspect actual artifacts. Keep implementation, execution evidence and external acceptance separate.

`data/v6/spec.json` is a reference snapshot, not a live configuration input. `PathwaySpec` is the default structural specification; the analysis driver passes explicit scenario instances. `extra_rescue` is conditional on otherwise locally retained infants after successful video, not an absolute percentage-point increase among all consultations.
