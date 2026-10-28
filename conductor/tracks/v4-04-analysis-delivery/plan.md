# Regenerated decision analysis and publication artifacts: implementation plan

**Global constraints:** no new clinical inputs; Polars-only DataFrame engine; no hidden environment installation, remote push, relaxed acceptance thresholds or manufactured lockfile.

**Review focus:** stale caches; deleted inputs; false passes from missing tools; duplicated suites; missing artifact-to-analysis links.

## Task 1: Rerun all existing analyses with unchanged protected inputs

**Status:** accepted. **Evidence:** `analysis_run.txt; 8×20,000 draws, 58 scenarios`.
Files: `scripts/run_v2.py; outputs/v4`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python scripts/run_v2.py --out outputs/v4 --iterations 20000` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 2: Check default-result parity, scenario inventory and analysis coverage

**Status:** accepted. **Evidence:** `analysis_audit.json: input preservation and default-output parity`.
Files: `quality/analysis_checks.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_analysis_checks.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 3: Assess Monte Carlo numerical stability without changing priors

**Status:** accepted. **Evidence:** `mc_precision.csv and six independent seeds; diagnostic only`.
Files: `scripts/complete_analysis_v4.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python scripts/complete_analysis_v4.py` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 4: Create refreshed plots, tables, evidence report and two-page CHHHS plan

**Status:** accepted. **Evidence:** `two-page plan, supplement, workbook, 14 figures and 14 slides`.
Files: `scripts/build_documents_v4.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python scripts/build_documents_v4.py` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 5: Render and visually inspect documents, figures and presentation

**Status:** accepted within rendered scope. **Evidence:** `document/slide renders and workbook inspection`.
Files: `verification/v4/visual`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `document render tools; manual visual inspection` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 6: Run final checks; commit, bundle and restore repository

**Status:** pending final restoration. **Evidence:** `package_v4.py; final bundle restore test follows commit`.
Files: `verification/v4`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m pytest -q; git bundle verify` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.
