# Generated document metadata (`docProps`)

Generated Office documents must not carry the personal or corporate metadata of the
templates and originals they are built from. `scripts/document_metadata.py` is the single
place that neutralises it; every generator that writes a `.docx`, `.pptx` or `.xlsx`
routes its save through it.

| Property | Value |
|---|---|
| Helper | `scripts/document_metadata.py` |
| Neutral value | `NEUTRAL_AUTHOR = NEUTRAL_COMPANY = "Neocam evaluation"`; `Template` is cleared |
| Library path | `save_neutralised(document, path)` → sets `core_properties` via python-docx/python-pptx, saves, then strips residual archive metadata |
| Archive path | `neutralise_archive_metadata(path)` → deterministic pass over `docProps/core.xml` and `docProps/app.xml` for any OOXML container |
| Test | `tests/test_document_metadata.py` |
| Receipt | `verification/v13/burndown/document-metadata.md` |

## Why it is needed

`assets/Briefing_note.docx` and `assets/chhhs-powerpoint-template.pptx` are authentic
corporate files. Their `docProps/core.xml` names the people who last edited them, and the
PowerPoint template's `docProps/app.xml` names the organisation. python-docx and
python-pptx preserve those parts on save, so before this helper every generated document
inherited the names. The privacy gate (`quality/privacy.py`) deliberately does not detect
personal names, so the leak passed silently.

## Call sites

Every OOXML generator calls the helper at its save, one line:

- `save_neutralised(...)`: `scripts/build_current_report.py`, `scripts/build_documents_v4.py`,
  `scripts/build_documents_v5.py`, `scripts/build_documents_v6.py`,
  `scripts/build_documents_v7.py`, `scripts/build_memo.py`, `scripts/build_reports_v2.py`.
- `neutralise_archive_metadata(...)`: `scripts/build_workbook.py`,
  `scripts/build_workbook_v2.py`, `scripts/build_workbook_v4.py`,
  `scripts/build_workbook_v5.py`, `scripts/build_workbook_v6.py`,
  `scripts/build_workbook_v7.py` (artifact_tool exposes no core-properties API).

The import is tolerant of both invocations (`python -m scripts.<generator>` and
`python scripts/<generator>.py`) so a generator works either way.

## Historical artefacts

Retained outputs (below `outputs/`) and supplied originals (below `sources/original/`) are
evidence and are **not** rewritten. New generations are clean; historical artefacts are
disclosed rather than silently altered. See the receipt for the counts.
