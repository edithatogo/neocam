# Neocam / Panda Vision

Early model-based economic evaluation of regional neonatal video consultation. This is a research decision model, not clinical guidance, an approved device specification or a validated prediction system.

## Current source and outputs

`config/reference.json` resolves the actual parameter, pathway and equipment-estate inputs. `data/parameters.json` is live; `config/pathways.json` is live; `data/v6/spec.json` remains a historical reference snapshot. Unknown fields, duplicate keys and invalid sites fail before execution.

```bash
# In the verified project environment; use a NEW output directory.
python -m scripts.reproduce --output outputs/reproduction --office
python -m quality.artifacts verify --output outputs/reproduction
python -m quality.cli --profile full --evidence-version v12
```

`--office` adds Word/PDF/PowerPoint reports using private supplied CHHHS assets. PDF conversion requires LibreOffice. The current path uses repository-relative assets, no host skill directory. CSV/JSON are the calculation tables; this release does not provide a newly certified recalculating Excel model.

Reference outputs: `outputs/v12/current_report.md`, current memo/presentation, CSV tables and figures. `release_manifest.json` binds actual output bytes to the generating inputs. Historical versioned artifacts are preserved, but the old age-discounted utility table is superseded by the current age-11 output.

## Dependency and assurance boundary

NumPy is used for numerical arrays. Only Polars is permitted as a DataFrame engine; pandas/xarray are excluded from project imports and the intended resolved environment. Model, optional research/reporting, tests and assurance dependencies are separate. The observed reporting environment is documented; it is not asserted to be latest or transitively locked.

A genuine `uv.lock` is still required. Ordinary tests on the available host do not certify the declared pinned stack, Gitleaks, mutation/property tools, type checkers or hosted CI. Missing required tools remain blocked. Current source and generated-output fingerprints are separately captured in the unified receipt; final execution results live in `verification/v12/` rather than being copied into mutable source context.

## Conductor

Start at `conductor/runbook.md`. Four bounded v12 tracks address execution/accounting, outputs/provenance, portable delivery and scientific validation. Predecessor records are historical evidence, not automatically reopened tasks. Clinical effects, source originals, independent review and institutional approvals remain separate acceptance questions.

## Private recovery

Authorised destination: `edithatogo/neocam`, existing draft PR #3. Full remote history/source/artifact migration remains incomplete until an exact inventory proves otherwise. The full private bundle preserves the original history. Never force-push main, claim an incomplete checkout passed the full suite, or publish corporate/licensed assets without permission. No patient-level records are part of this model.
