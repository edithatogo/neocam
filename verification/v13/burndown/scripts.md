# scripts/ ruff burn-down — result and integrity audit (2026-10-31)

## Result

| Metric | Value |
|---|---|
| Findings before | 16,518 (13,670 auto-fixable) |
| Findings after | **0** (`ruff check scripts` → "All checks passed!") |
| Format | 30 files already formatted, 0 to reformat |
| Files cleared | 30 of 37 modified (all files with findings) |
| Full suite | 678 passed (0 failed) |

Work was split across three agents by file group: build_workbook*/build_documents_*
(5,536), analyse_*/audit/archive (4,959), plots/reports/misc (5,322).

## Independent integrity audits (run by the parent, not the agents)

1. **Numeric-literal AST sweep** — for every modified script, the multiset of numeric
   literals in `HEAD` was compared with the working tree:
   `checked 30 scripts: numeric differences in 0`.
2. **Comparison-operator and tolerance-call profile** — multiset of `Compare` operators
   and of `isclose`/`allclose`/`approx` calls, `HEAD` vs working tree:
   `scripts with introduced/removed tolerance calls: 0`.
   Only differences found anywhere: `x not in ('manifest.json',)` → `x != 'manifest.json'`
   (identical), a local variable rename, and tuple → set membership in
   `archive_sources_v7.py` (all semantically equivalent).
3. **Diff inspection for output-affecting edits** — every `figsize`/`dpi`/`savefig`/
   `title`/`xlabel`/`ylabel`/`sheet_name`/`to_excel`/`write_text`/output-path line in the
   scripts diff was reviewed; filenames, JSON `indent` values and write targets unchanged.

## Corrections made during the audit (four sites, all in published-report selection)

Three agents had resolved `RUF069` (float equality) by **introducing tolerances** into
report/plot selection code, which would change which rows a published document displays
without any test evidence. All were reverted to exact comparison with a per-line justified
ignore (`# ruff: ignore[float-equality-comparison] -- published selection must not change`),
keeping the named constants introduced for `PLR2004`:

- `scripts/build_current_report.py` (3 comparisons)
- `scripts/plot_v7.py` (3 comparisons)
- `scripts/plot_current.py` (2 comparisons: `utility_difference`, `fraction_consultations_improved_assumed`)
- `scripts/build_documents_v7.py` (1 comparison; constant restored to the original `int` 50000)

Note this is the opposite of `src/audit_v7.py`, where `RUF069` exposed a **genuine** defect
(a reference parameter differing by 1e-12 was silently redrawn) that now carries a
failing-first test. Script sites have no such evidence, so behaviour is preserved.

## One pre-existing tolerance, left exactly as HEAD had it

`scripts/analyse_v5.py` protected-parity guard (`raise AssertionError("Original Panda PSA
changed")`) has carried `np.isclose(..., rtol=1e-12, atol=1e-7)` since `HEAD`. An initial
audit pass tightened it to exact equality; that was itself a behaviour change, so it was
restored to the pre-existing form — recorded here so the tolerance is visible rather than
implied. `scripts/analyse_v7.py:473` similarly retains its pre-existing
`np.flatnonzero(np.isclose(m, m.max(), rtol=0, atol=1e-9))` max-tie selection.

## Suppression surface (for review)

Inline ignores added in `scripts/` are per-line with a rule name and reason. The largest
group is authored report prose that must stay verbatim: `line-too-long` and
`ambiguous-unicode-character-string` (en dash, ×, ☒ used in published narrative), plus
`implicit-namespace-package` (one per file, `scripts/` has no `__init__.py`),
`private-member-access` (python-docx internals), `print` (status output), and
subprocess/path rules for fixed git/CLI commands. No global or per-file ignore was added
for `scripts/`; `pyproject.toml` was not modified by this phase.
