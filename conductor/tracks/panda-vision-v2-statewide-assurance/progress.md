# Execution ledger
- Baseline:5tests passed; no existing CI or lock found.
- Evidence: full2022 birth table,7principal abstracts, QHfunding, public air cost and CPI bridge verified.
- TDD:28expected failures before v2 implementation; first implementation33passed/1failed. Ruling: zero-resource test omitted delayed-rescue cost; corrected test to set rescue_rate=0, not the economically correct code.
- Additional regression: critical-only case mix initially ignored by PSA; failing test reproduced; fixed to preserve explicit zero-share strata and input baseline probabilities.72tests now pass; v2branch coverage96%.
- Assumptions: structured local elicitation removed as prerequisite. Priceyear of aircost assumed2019; source has2018–2019 audit context;2018sensitivity included. Data are historical, not a complete current2026facility census.
- CI: SHA-pinned current actions; Python3.13/3.14/3.15target matrix; direct latest pins; hash-resolution workflow; property/security gates and approval-only release. External DNS prevents installation, hash-lock resolution, actual Conductor checkout and hosted runs. Do not mark these passed.
- Author self-review only; no subagent reviewer.

Final local delivery:75tests pass,96% core branch coverage. Three new assurance-scope tests observed RED then GREEN; partial --ci model receipts can no longer claim full release assurance. Two-page CHHHS memo,12-slide deck,nine-page evidence supplement,workbook and CSVs generated. Author self-review only. Ruling: classify native-table EMU helper warnings as representation mismatches; final OOXML/slide overflow test passes. Corporate background placeholders removed; source IDs reconciled. Online gates/submodule remain blocked, not waived.
