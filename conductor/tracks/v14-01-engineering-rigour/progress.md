# Execution ledger — v14-01 engineering rigour

1.0 Design authority recorded in `conductor/v14-design.md`: measured dependency audit
(installed versions), the "foot in two camps" decisions D1–D5 with options, rationale,
tradeoffs and contingencies, and the deliberate non-violations that must not be
"fixed" later.

1.1 reportlab incorporation: **DONE**. `scripts/build_current_report.py` gained
`build_pdf(output, lines)` (plus `_pdf_flowables`, `_pdf_table`, `_markdown_cells`,
`_inline_markup`, `_pdf_page_furniture`), fed from the same authored `lines` the markdown
sibling uses, with reportlab imported lazily. Artefact: `outputs/v13-primary/current_report.pdf`,
5,779 bytes, 2 A4 pages, real table flowables with a repeated header row and page numbers.
Determinism via `SimpleDocTemplate(..., invariant=True)` — two runs produced identical bytes
(`947d89a4…`). Tests in `tests/test_reportlab_document.py` (5) assert the producer is
ReportLab (not matplotlib), the absence of images, byte-determinism, the disclosed caveats
in the decoded text, and registration through `artifacts.output_inventory()`. It is not a
second renderer for the same purpose: figure PDFs remain matplotlib's, and the optional
`soffice` DOCX→PDF path is non-byte-stable. Receipt: `verification/v13/burndown/reportlab-document.md`.

1.2 Testing depth — LANDED (with one open performance defect). pytest-socket 0.8.1,
pytest-timeout 2.4.0, pytest-randomly 5.0.0, time-machine 3.6.0 and doctest execution are
declared and configured; `pydantic==2.14.2` is pinned directly (assurance group, no new
package: it already arrived via scalene) and `[tool.coverage.run] core = "sysmon"` is
applied. Suite is green at **1,065 passed**.
  **Open defect**: suite wall time rose from ~6 s to ~18 s, and profiling attributes 14.2 s
  of it to `quality/privacy.py::_inspect_line`, which runs 1.22 million times (five separate
  regex passes per line) over ~1,600 tracked files. Because pytest-gremlins executes the
  suite once per mutant (1,250 mutants against a 1,800 s gate budget), this must be reduced;
  the fix must preserve findings and skip semantics exactly.

1.3 Static-analysis depth — NOT STARTED (needs `pyproject.toml`, which is free now that the
dependency-owning agent has finished).


1.4 Experimental trials — measured outcomes (each measurement retained in
`verification/v13/burndown/experimental-trials.md`):
- `COVERAGE_CORE=sysmon` ADOPT: 6.53 s → 6.06 s with byte-identical coverage
  (94.17%, 153 missed, 36 partial branches). Applied as `[tool.coverage.run] core = "sysmon"`.
- `uv pip check` ADOPT as a cheap gate: passes in 4 ms; covers the half-synced-venv
  failure that otherwise surfaces as confusing test/typing errors.
- `pip-audit --vulnerability-service=osv` SKIP: identical results to the default service
  (74 packages, 0 vulnerabilities), so there is no evidence to justify the change.
  Contingency: revisit if a PyPI-advisory miss is observed.
- `uv export --frozen` HOLD: works (180 lines) but would duplicate the cyclonedx SBOM
  with no consumer. Adopt only when a concrete consumer exists.
- pytest-gremlins `--gremlin-batch` REJECT: A/B on `src/sensitivity.py` measured 42.2 s
  default versus 175.0 s batched, and batching reported fewer mutants (76 vs 79
  accounted), so it costs time and distorts the reconciled summary.
- Mutation sharding across CI jobs NOT VIABLE: `quality.checks mutation` reconciles one
  report (`total = zapped + survived + timeout + error + pardoned`), and
  pytest-gremlins provides no report merge.
- matplotlib.typing PENDING in the scripts pass (ColorType confirmed present in 3.11.2;
  ~7 `reportUnknownMemberType` suppressions at matplotlib call sites are removable).
- hypothesis `target()`/`event()` plus a seeded non-derandomised profile: SCHEDULED
  (the current `panda_ci` profile sets `derandomize=True`, so the suite never explores new
  examples, and `deadline=None`, which disables a check).

1.5 Validation replacement — DECISION TAKEN: use **pydantic 2.14.2** (latest release,
already the installed version, arriving transitively via `scalene`). Pinning it directly
removes the coupling where the harness's validation engine existed only because a
profiler needed it, at zero new package cost. The harness migration is its own follow-up
and must preserve the exact inner error text the suite asserts. msgspec rejected: it would
be a genuinely new package for no measured gain over an already-present dependency.

1.2–1.3 testing and static-analysis depth: IN PROGRESS (pytest-socket, pytest-timeout,
pytest-randomly, time-machine, doctests; vulture/deptry/architecture contracts/snapshot
regression to follow once the dependency-owning agent releases `pyproject.toml`).

Context from the preceding engineering wave (already landed, see
`verification/v13/burndown/`): Python 3.15-only policy; ruff/ty/basedpyright at maximum
strictness; SHA-pinned hardened CI with CodeQL, dependency-review, Scorecard and
attestation; mutation score raised from 69.78% to 99.52% (gate green); 1,027+ tests.

