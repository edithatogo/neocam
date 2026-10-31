# Current report PDF (`current_report.pdf`)

`scripts/build_current_report.py` writes three siblings from one authored line list:
`current_report.md`, `current_report.html` and `current_report.pdf`. The PDF is the
paginated form of the same text; it adds no content the markdown sibling does not disclose.

| Property | Value |
|---|---|
| Generator | `reportlab` 5.1.0 `reportlab.platypus` (declared in the `reporting` extra) |
| Code | `build_pdf()` in `scripts/build_current_report.py`, called from `build()` |
| Location | `outputs/<scope>/current_report.pdf`, beside the md and html siblings |
| Document | A4, 2 pages, Helvetica/Helvetica-Bold base-14 fonts, running footer rule with page numbers, real table flowables whose header row repeats across page breaks |
| Measured | 5,779 bytes for `outputs/v13-primary/current_report.pdf` |
| Determinism | `SimpleDocTemplate(..., invariant=True)` plus fixed footer text; reportlab otherwise embeds creation/modification dates and a file fingerprint |
| Figures | None. The PDF is the paginated text document, like the markdown sibling; figures stay in the HTML (SVG) and the deck (PNG). |
| Test | `tests/test_reportlab_document.py` |

## Why this is not a second PDF renderer for the same purpose

- matplotlib emits one PDF *per figure* through `savefig`; it does not paginate flowing text,
  headings or tables and emits no page furniture.
- The `--office` path converts the private-template DOCX to PDF with `soffice`, an optional
  external binary whose output is not byte-stable. The reportlab path needs only a Python
  dependency, runs inside the ordinary report build, and is byte-identical across runs.

## Regenerating and verifying

```
uv run --frozen --no-sync python -m scripts.build_current_report --output outputs/v13-primary
shasum -a 256 outputs/v13-primary/current_report.pdf
```

Two consecutive runs must print the same digest. `quality.artifacts.output_inventory()`
discovers the file automatically, so a release seal binds it exactly like the md and html
siblings, and `scripts/build_current_report.py` is already pinned by
`quality.artifacts.calculation_inputs()`.
