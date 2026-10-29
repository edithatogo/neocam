# Exact multidimensional sensitivity and explanatory learning — detailed plan


Source specs and prior track history remain immutable. Current execution receipts decide acceptance, not this checklist.


## 1. [x] Declare bounded design with provenance

Files: `data/v5/sensitivity_ranges.csv; src/sensitivity.py`

Contract: Twelve explicit coordinates; ranges are not empirical probability distributions

Check: `python -m pytest tests/test_v5_sensitivity.py -q`

Status/evidence: Implemented and tested.


## 2. [x] Execute paired and structural PSA

Files: `scripts/analyse_v5.py; outputs/v5/psa_strategy_summary.csv`

Contract: 18 structures × 20,000 paired draws; 6 repeat-seed checks

Check: `python scripts/analyse_v5.py`

Status/evidence: Executed using recorded installed scientific versions; analysis_run.txt.


## 3. [x] Execute exact one-, two-, four- and five-way designs

Files: `src/sensitivity.py; outputs/v5/*way*.csv`

Contract: Pilot/state one-/two-way; pilot joint grids; k-way frequency is not probability

Check: `python scripts/analyse_v5.py`

Status/evidence: 2,520 one-way rows; 7,688 two-way points; 3,125 five-way and 2,401 four-way points.


## 4. [x] Validate input-only clustering and independent variance design

Files: `scripts/analyse_v5.py; outputs/v5/sobol_indices.csv`

Contract: Fit clustering on input training set only; retain unstable clusters; Sobol independent design distinct from PSA

Check: `python scripts/analyse_v5.py`

Status/evidence: Executed: weak clustering explicitly reported; 86,016 variance-design evaluations.


## 5. [x] Validate decision-focused explanation, not just R-squared

Files: `outputs/v5/heldout_predictions.csv; verification/v5/validation_model_selection.json`

Contract: Use selection sample for method choice; retire diagnostic holdout; final fresh holdout seed504

Check: `python scripts/analyse_v5.py`

Status/evidence: 95.0% held-out agreement, mean regret60, worst8970; exact kernel remains authoritative.


## 6. [x] Verify output manifest and boundary contracts

Files: `tests/test_v5_analysis_integrity.py; tests/test_v5_strategies.py`

Contract: Manifest excludes self-hash; typed/finite inputs and eligibility checks

Check: `python -m pytest tests/test_v5_analysis_integrity.py tests/test_v5_strategies.py tests/test_v5_sensitivity.py -q`

Status/evidence: Executed; RED/GREEN receipts retained.

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
