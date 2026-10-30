# Execution and accounting consistency implementation plan

**Goal:** Execution and accounting consistency.
**Architecture:** existing exact pathway model, small standard-library adapters, explicit source and artifact provenance.
**Stack:** Python/NumPy; optional reporting libraries; existing assurance tools.
**Spec:** `v12-01-execution-accounting/spec.md`.

## 1. configuration
Create src/configuration.py and config/reference.json; strict complete schemas; source hashes; unknown/duplicate JSON fields rejected. Parameters come from data/parameters.json; pathways from config/pathways.json. Audit the resolved values, not merely matching stale files.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 2. estate
Create src/equipment.py and config/equipment_estate.json. Known pilot ownership and remaining-life assumptions feed both retained-capital evaluation and annual mixed-estate replacement schedules.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 3. driver
Wire scripts/analyse_v7.py to the resolved configuration and configurable fresh output directory. Preserve current reference numerical outputs. Make import side-effect free; retain historical outputs unchanged.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

