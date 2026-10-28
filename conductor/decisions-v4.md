# V4 decisions

- User authorises implementation, not a new clinical model.
- Current tool installation remains DNS-blocked after a fresh check. Do not spend repeated retries on an unchanged blocker.
- Keep serial execution until plugin benchmarks establish an improvement.
- Full suite once under coverage supplies both pytest and coverage evidence.
- Author-only skill review is not independent agent behaviour evaluation.

- Ruling: keep test execution serial; optional selection/parallel plugins cannot be benchmarked without installation. No performance benefit attributed to them.
- Ruling: report the measured plain+covered workload sum, not an uncompleted repeated end-to-end benchmark.
- Ruling: diagnostic authoring is split into complete_analysis_v4.py, build_documents_v4.py, build_workbook_v4.py and build_slides_v4.js; preserves a small numerical runtime.
- Ruling: skill validation is contract tests plus author review only; no fabricated subagent results or global installation.
