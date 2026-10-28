# Conductor v5 — comparative evaluation and sensitivity

28 October 2026. Implementation and acceptance are separate states.

---
# v5-01-comparators
# Five complete service configurations — detailed plan


Source specs and prior track history remain immutable. Current execution receipts decide acceptance, not this checklist.


## 1. [x] Define non-overlapping strategies

Files: `data/v5/strategies.csv; evidence/v5/comparator_assumptions.json`

Contract: Telephone baseline and four complete video configurations; component-only prices excluded

Check: `python -m pytest tests/test_v5_strategies.py -q`

Status/evidence: Implemented; focused tests passed.


## 2. [x] Extract paired random inputs without changing Panda results

Files: `src/statewide.py::sample_inputs`

Contract: Same random draw order and original default PSA arrays

Check: `python -m pytest tests/test_v5_strategies.py::test_psa_preserves_previous_panda_draws -q`

Status/evidence: Passed; full default summary parity also recorded in results_v5.json.


## 3. [x] Implement exact five-arm kernel adapter

Files: `src/strategies.py::compare_inputs; compare; compare_psa`

Contract: Same effects/cost draws across strategies; telephone incremental zero but same activity

Check: `python -m pytest tests/test_v5_strategies.py -q`

Status/evidence: Implemented; focused tests passed.


## 4. [x] Separate sunk, attributed and procurement capital

Files: `src/strategies.py::compare_inputs`

Contract: Capital allocation must not reduce full purchase payment; sunk affects only existing arm

Check: `python -m pytest tests/test_v5_strategies.py -q`

Status/evidence: Implemented and tested.


## 5. [x] Report paired choices, regret and cost-only EVPI

Files: `src/strategies.py::summarise`

Contract: Fractional ties; common-draw comparisons; expected value distinct from P(optimal)

Check: `python -m pytest tests/test_v5_sensitivity.py -q`

Status/evidence: Implemented and tested.


## 6. [x] Preserve original scientific inputs and outputs

Files: `evidence/protected_inputs_v4.json; outputs/v5/results_v5.json`

Contract: Nine protected files unchanged; Panda pilot/state reference PSA matches v4

Check: `python -m quality.checks inputs`

Status/evidence: Primary verification recorded in verification/v5/full/inputs.txt.


---
# v5-02-sensitivity
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


---
# v5-03-publication
# Publication-ready presentation and honest release boundaries — detailed plan


Source specs and prior track history remain immutable. Current execution receipts decide acceptance, not this checklist.


## 1. [x] Verify current journal fit and requirements

Files: `evidence/v5/journal_targets.csv; docs/publication_strategy_v5.md`

Contract: Primary publisher scope/format/fee verification; no invented impact/acceptance rates

Check: `Read source register and compare against publisher pages`

Status/evidence: Completed 28 October 2026; uncertain fees marked unverified.


## 2. [x] Regenerate charts, workbook, memo and slides

Files: `scripts/plot_v5.py; build_documents_v5.py; build_slides_v5.js; build_workbook_v5.py`

Contract: Same versioned numeric outputs; workbook formulas audited; complete CSVs retained

Check: `Run named scripts; render DOCX/PPTX; inspect exported XLSX`

Status/evidence: Completed; two-page plan, eleven-page supplement, twelve slides, eighteen-sheet workbook, fifteen figures.


## 3. [x] Extend existing assurance scope without duplicate suites

Files: `quality/cli.py; quality/checks.py; pyproject.toml; tests/test_v5_assurance_scope.py`

Contract: New modules in mutation scope; analysis script in both typecheck scopes; current receipts do not overwrite v4

Check: `python -m quality.cli --profile full`

Status/evidence: Execution evidence is authoritative at verification/v5/full/receipt.json; implementation is not toolchain acceptance.


## 4. [ ] Complete connected latest-toolchain and hosted acceptance

Files: `uv.lock; extensions/conductor; .github/workflows/ci.yml`

Contract: Resolve real lock, install targets, checkout submodule, run all gates and hosted checks

Check: `uv lock; uv sync --locked --group assurance --extra tabular --extra research; python -m quality.cli --profile full`

Status/evidence: BLOCKED: network unavailable; no hosted run or remote push claimed.


## 5. [ ] Complete independent source and structural review

Files: `docs/publication_strategy_v5.md`

Contract: Critical full texts, clinical/economic independent review, governance/authorship/data-rights statements

Check: `Independent review and documented institutional determination`

Status/evidence: OPEN: no trial or structured elicitation prerequisite; no invented reviewer approval.


## 6. [x] Archive and verify working handoff

Files: `verification/v5; source ZIP; Git bundle`

Contract: Restore and rerun ordinary suite; clean tracked tree; no fonts/secrets or unauthorized public deposit

Check: `git bundle verify; restored python -m pytest -q; ZIP test`

Status/evidence: Final packaging evidence in verification/v5/packaging.json.
