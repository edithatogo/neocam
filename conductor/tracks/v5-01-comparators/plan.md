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

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
