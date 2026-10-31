# Task 1.1: reportlab incorporation — paginated current-report PDF (2026-10-31)

Owner decision: `reportlab` is kept and used. The defect was "declared in the `reporting`
extra, imported by nothing"; the fix gives it the one job no sibling does — a paginated
document with flowing text, headings, tables that repeat their header across page breaks,
and page furniture with page numbers.

## What changed

| Item | Value |
|---|---|
| Code | `scripts/build_current_report.py`: `build_pdf(output, lines)` plus `_pdf_flowables`, `_pdf_table`, `_markdown_cells`, `_inline_markup`, `_pdf_page_furniture` |
| Wiring | `build()` calls `build_pdf(output, lines)` with the same authored `lines` the markdown sibling uses, so content cannot diverge |
| Artefact | `outputs/v13-primary/current_report.pdf` (scope named by `config/assurance.json`) |
| Measured | **5,779 bytes, 2 A4 pages**, Helvetica + Helvetica-Bold base-14 fonts, no embedded figure raster |
| Siblings | `current_report.md` 3,598 B, `current_report.html` 4,823 B (unchanged by this task) |
| Test | `tests/test_reportlab_document.py` (5 tests, all pass) |

## Determinism

`SimpleDocTemplate(..., invariant=True)` (reportlab's invariant mode), plus footer text with
no clock reading. Without it reportlab embeds `CreationDate`/`ModDate` and a file fingerprint.

Two consecutive generator runs, same input:

```
u$ python -m scripts.build_current_report --output outputs/v13-primary
947d89a44d401caa576e1ecf10db7f1b7ca20f176226f891ee29f263fc766aa5  outputs/v13-primary/current_report.pdf
u$ python -m scripts.build_current_report --output outputs/v13-primary
947d89a44d401caa576e1ecf10db7f1b7ca20f176226f891ee29f263fc766aa5  outputs/v13-primary/current_report.pdf
u$ cmp run1.pdf outputs/v13-primary/current_report.pdf && echo IDENTICAL
IDENTICAL
```

`current_report.md` and `current_report.html` digests are unchanged before and after the run
(`62d868a7…`, `b99ed597…`), so this task added a file and rewrote nothing.

## Is it a duplicate PDF path?

No.

- matplotlib exports one PDF *per figure* (`savefig`); it does not paginate text, headings or
  tables and emits no page furniture.
- the `--office` path converts the private-template DOCX to PDF with `soffice`, an optional
  external binary that is not byte-stable and is skipped when absent. The reportlab path
  needs only a Python dependency and is byte-identical across runs.
- against the siblings: markdown has no pagination or page numbers, HTML has no print
  pagination and needs a browser; neither gives an archivable fixed-layout document.

## Registration

`quality.artifacts.output_inventory()` globs the whole output scope, so the new file enters
`release_manifest.json` on the next seal with no code change; `scripts/build_current_report.py`
was already pinned by `calculation_inputs()`. **No inventory test enumerates the current-report
file list** (checked `tests/test_v4_analysis_checks.py`, `tests/test_v12_artifacts.py`,
`tests/test_v13_pipeline.py`: they assert row counts, hashes and failure behaviour, not a file
set), so nothing was updated — instead `tests/test_reportlab_document.py` now asserts the PDF
appears in `artifacts.output_inventory()`. The manifest itself is **stale** (script digest
moved) and must be re-sealed by the parent at wave end; nothing was sealed here.

## Verification (exact output)

1. `ruff check scripts tests` → `All checks passed!` while only this task's files were new.
   The final run reports `Found 3 errors`, **all in the other agent's in-flight
   `tests/test_privacy_scan.py`**; `ruff check scripts/build_current_report.py
   tests/test_reportlab_document.py` → `All checks passed!` and
   `ruff format --check` on those two files → `2 files already formatted`.
2. `ty check` → `All checks passed!`. `basedpyright` → `31 errors`, **all in
   `tests/test_privacy_scan.py`**; scoped to this task's two files →
   `0 errors, 0 warnings, 0 notes`. (An earlier run saw 3 ty / 6 basedpyright errors in the
   other agent's `quality/privacy.py`; that file is clean now.)
3. `python -m pytest -q -p no:cacheprovider` → at the first stable run **1031 passed**, i.e.
   the 1027 baseline plus this task's then-4 tests; final run **1065 passed** (this task's 5
   tests plus the other agent's 28 + 67 tests in `tests/test_privacy_scan.py` and
   `tests/test_mutation_statewide.py`). No failure is in this task's files; at an intermediate
   point their `test_mutation_statewide.py` was red with
   `np.array_equal(ones(4), ones(4)) == False` (exact float equality in their new test),
   reported, not fixed.
4. Two generator runs diffed: identical bytes, digest above (both runs).
5. `python -m quality.checks context` → `{"check": "context", "errors": []}`.

## Deliberately not done

- No figure raster in the PDF: the markdown sibling has none, and matplotlib owns figures.
- No `outputs/v12` regeneration (historical; runbook says never overwrite retained analyses).
- No seal, no `pyproject.toml`/`uv.lock`/`src/`/`quality/` edits, no git commands.
- No new scientific content, parameter, or clinical claim.

## Next executable command

```
uv run --frozen --no-sync python -m pytest -q -p no:cacheprovider tests/test_reportlab_document.py
```
