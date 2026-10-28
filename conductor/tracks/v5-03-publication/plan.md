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
