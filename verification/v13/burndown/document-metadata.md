# Task: generated-document metadata neutralisation — privacy hygiene (2026-10-31)

Finding (from the privacy gate's own documented limits): the gate does not detect personal
names, so tracked OOXML core properties (`dc:creator`, `cp:lastModifiedBy`, and `Company`
in `docProps/app.xml`) carried names silently. This task neutralises metadata on **new**
generations and discloses the historical artefacts without rewriting them.

## Leak inventory (counts, values redacted)

30 tracked OOXML artefacts scanned (`.docx`/`.pptx`/`.xlsx`).

| Class | Count | Detail |
|---|---:|---|
| Non-neutral `dc:creator`/`cp:lastModifiedBy` | 14 | 13 carry a personal name (3 distinct personal-name values, each `X…` length 15–18); 1 carries the corporate organisation name (length 49) |
| Corporate `Company` value | 4 | `assets/chhhs-powerpoint-template.pptx`, `sources/original/chhhs-powerpoint-template.pptx`, `outputs/v12/Neocam_current_presentation.pptx`, `outputs/Panda_Vision_economic_evaluation_CHHHS.pptx` |
| Neutral creator, corporate `subject`/`Template` | 10 | creator is `python-docx` or `Evaluation working draft`; `subject`/`Template` from the CHHHS template |
| No `docProps` at all (clean) | 6 | all six `.xlsx` (artifact_tool writes no core properties) |

Files with a personal name in `dc:creator`/`cp:lastModifiedBy` (redacted): the two `assets/`
templates, the three `sources/original/` originals, `outputs/Panda_Vision_economic_evaluation_briefing_note.docx`,
`outputs/v12/Neocam_current_plan.docx`, `outputs/v12/Neocam_current_presentation.pptx`,
`outputs/v2/Panda_Vision_CHHHS_brief_v2.docx`, and
`outputs/v4|v5|v6|v7/Panda_Vision_two_page_plan_v*.docx`.

## What changed

| Item | Value |
|---|---|
| Helper | `scripts/document_metadata.py` (dependency-free besides the already-used python-docx/python-pptx) |
| Neutral value | `NEUTRAL_AUTHOR = NEUTRAL_COMPANY = "Neocam evaluation"`; `Template` cleared; free-text core fields (`subject`, `keywords`, `description`, `category`, `status`, `identifier`, `language`) cleared |
| Library call | `save_neutralised(document, path)` sets `core_properties`, saves, then strips residual archive metadata |
| Archive call | `neutralise_archive_metadata(path)` deterministically rewrites `docProps/core.xml` + `docProps/app.xml`, preserving member order, compression and timestamps; idempotent |
| Call sites | `save_neutralised`: `build_current_report.py`, `build_documents_v4/5/6/7.py`, `build_memo.py`, `build_reports_v2.py`. `neutralise_archive_metadata`: `build_workbook.py`, `build_workbook_v2/4/5/6/7.py` |
| Test | `tests/test_document_metadata.py` (5 tests) |

## Verification (exact output)

**1. Reproduce the leak — fresh generation from a template (before state, redacted):**

```
### DOCX (assets/Briefing_note.docx)
  BEFORE creator        = H*************** [len=16]
  BEFORE lastModifiedBy = J**************  [len=15]
  BEFORE Company        = (empty)
  BEFORE Template       = N***** [len=6]
### PPTX (assets/chhhs-powerpoint-template.pptx)
  BEFORE creator        = K***************** [len=18]
  BEFORE lastModifiedBy = K***************** [len=18]
  BEFORE Company        = C************************************************ [len=49]
  BEFORE Template       = m******************** [len=21]
```

**2. After the fix — same generation into a temp directory:**

```
  AFTER creator        = 'Neocam evaluation'
  AFTER lastModifiedBy = 'Neocam evaluation'
  AFTER Company        = 'Neocam evaluation'
  AFTER Template       = ''
  AFTER /Users or /home in metadata: False
  AFTER second neutralise pass changed anything: False
```

**3. `uv run --frozen --no-sync python -m pytest -q -p no:cacheprovider`** → `1085 passed in 20.98s`
(1080 prior baseline + this task's 5 tests). Nothing failed; no concurrent-agent breakage was
present at the run.

**4. Static analysis:**

```
ruff check .                                    → All checks passed!
ruff format --check src scripts quality tests sources → 126 files already formatted
ty check --error-on-warning                     → All checks passed!
basedpyright                                    → 0 errors, 0 warnings, 0 notes
```

**5. Regeneration diff (metadata-only):** applying the fix's save-time change to retained
generated artefacts changes only the metadata parts; every content part is byte-identical.

```
outputs/v7/Panda_Vision_two_page_plan_v7.docx        members differing: ['docProps/app.xml','docProps/core.xml']  (33/35 identical)
outputs/v12/Neocam_current_presentation.pptx        members differing: ['docProps/core.xml','docProps/app.xml']  (93/95 identical)
```

`word/document.xml` (all numbers, tables and prose) is unchanged, so no published number or
text moves.

## Historical-artefact disclosure (non-destructive limitation)

14 tracked artefacts still carry non-neutral name metadata: the supplied originals under
`sources/original/`, the two private templates under `assets/`, and the retained outputs
listed above. They are retention evidence and were **not** rewritten. Policy: new generations
are clean; historical artefacts are disclosed here rather than silently altered. Because the
`assets/` templates are pinned by `quality.artifacts.SOURCE_FILES`, only
`scripts/build_current_report.py` among the pinned inputs changed digest here; the release
manifest is **stale** and must be re-sealed by the parent at wave end. Nothing was sealed.

## Text content that also leaks a path

No genuine filesystem path was found in the *text of any generated document*.

- `/home/tehb` matched in `outputs/v5/Panda_Vision_comparative_analysis_v5.xlsx` and
  `outputs/v5/Panda_Vision_comparative_supplement_v5.docx` is a false positive: it is the
  Sage journal home page `https://journals.sagepub.com/home/tehb`, an authored URL, not a path.
- `sources/original/A4-Report-1-light.docx` carries an external hyperlink target
  `file:///C:\Users\<user>\Downloads\test` in `word/_rels/document.xml.rels`. This is a real
  filesystem user path, but it is in a **source original** (retained evidence, not a generated
  document), so it is disclosed here and left unaltered rather than edited.

## Deliberately not done

- No rewrite of any retained output or supplied original.
- No `pyproject.toml`, `uv.lock`, `quality/`, `.github/`, `src/` edit and no git command.
- `scripts/build_slides*.js` (pptxgenjs) are out of the Python helper's reach; their decks
  carry the neutral creator `Evaluation working draft`, not a personal name, so no change was
  made there.

## Next executable command

```
uv run --frozen --no-sync python -m pytest -q -p no:cacheprovider tests/test_document_metadata.py
```
