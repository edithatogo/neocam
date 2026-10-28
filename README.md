# Panda Vision evaluation — v5 working handoff

Five complete neonatal consultation configurations: telephone, mobile teleconference, Panda Vision, fixed PTZ and proposed tablet/OBSBOT. A small NumPy cohort engine remains authoritative. Offline SciPy/scikit-learn analysis explores sensitivity and explains decisions; it does not produce clinical evidence.

Start with `conductor/runbook.md`. Current outputs are under `outputs/v5/`; original analyses remain under `outputs/v4/`. See the two-page plan, comparative supplement and publication strategy. No public deployment, hosted CI or independent review is claimed. Latest-toolchain acceptance remains incomplete.

## Preserved project documentation

# Panda Vision evaluation — v4

An existing-evidence neonatal video-versus-telephone economic evaluation, with an intentionally small numerical model and explicit assumptions. **Preliminary; not a clinical prediction tool or proof of savings.**

## Start here

- `conductor/current-state.json` and `conductor/runbook.md`: authoritative workflow and next gates.
- `outputs/v4/Panda_Vision_two_page_plan_v4.pdf`: two-page CHHHS evaluation plan.
- `outputs/v4/Panda_Vision_analysis_supplement_v4.pdf`: analysis, sources and limits.
- `outputs/v4/Panda_Vision_analysis_v4.xlsx`: inspectable result tables, not an Excel PSA engine.
- `outputs/v4/figures`: individual PNG/SVG figures; CSVs contain the full tables.
- `.agents/skills/maintaining-lean-ci`: portable skill and evidence-contract checker.

V4 preserves 27 economic parameters and default v2/v3 outputs. It removes duplicate testing, adds guarded local feedback and thin hooks/workflow checks, reruns the existing analyses, and adds numerical/break-even/equipment-life diagnostics without new clinical parameters.

Local ordinary tests and numerical checks pass. **Full locked latest-toolchain acceptance does not:** see `verification/v4/full/receipt.json`. The absence of packages, a real lock or submodule checkout is never treated as a successful check. No hosted CI, remote push, publication or permanent ChatGPT skill installation is claimed.

Use the runbook for environment setup, analysis, authoring and acceptance. Historical releases are preserved for provenance, not current status. Corporate template assets remain internal materials; do not publish without appropriate authority.
