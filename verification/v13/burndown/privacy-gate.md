# Privacy / personal-identifier gate (2026-10-31)

Track: `conductor/tracks/v14-03-ecosystem-integration`, phase/task 3.2. Owner
requirement: the repository is **public** and must be certain that tracked content
carries no personal or patient data. `gitleaks` covers secrets only.

## What was added

| Artefact | Role |
|---|---|
| `quality/privacy.py` | The scanner and its CLI; standard library only, no new dependency |
| `tests/test_privacy_scan.py` | Fixture sensitivity proof plus the real-tree assertion |
| `.github/workflows/privacy.yml` | Runs the scan, then re-proves sensitivity in CI |
| `Gate("privacy", ...)` in `quality/cli.py` | Enforced by the `pr` and `full` profiles |
| `privacy-gate.json` (this directory) | Receipt for the real tree: 0 findings |
| `privacy-fixture.json` (this directory) | Receipt for the synthetic fixture: 9 findings |

## Patterns implemented

| Rule | Shape required | Why it is safe on this tree |
|---|---|---|
| `email` | One mailbox, minus RFC 2606/6761 reserved domains and URL userinfo | The tree's only `@` form is `user:password@host` inside a test URL |
| `au_phone` | 10 digits, `02/03/04/07/08`, written grouped or with `+61` | 2,890 bare 10-digit runs exist here; a bare run is never a phone |
| `medicare_number` | The words Medicare/IHI/individual healthcare identifier, then 10-11 digits | Numeric rules are context-anchored, never bare |
| `tfn` | The words TFN/tax file number, then 8-9 digits | 56 checksum-valid `d{3} d{3} d{3}` groups exist in figure coordinates |
| `card_number` | Card words, then 13-19 digits, Luhn-valid | 1,259 Luhn-valid grouped 16-digit runs exist in chart text |
| `identifier_column` | A CSV header that names an identifier and holds identifier-shaped values | `patient_family_net` and `telephone_net` are strategy names, not identities |
| `identifier_key` | The same test for a JSON key | `"mobile"` here maps to a strategy object, not a phone number |

Exemptions (`Allowance`) exist but the list is **empty**: every historical false positive
is already excluded by a rule, so no exemption is currently justified. Each entry would
need a written reason; `unused_exemptions` fails the gate once an entry stops suppressing
anything, so an exemption cannot quietly widen the scan.

## Fixture proof

`tests/test_privacy_scan.py` writes a fake mailbox, landline, mobile, Medicare number,
TFN and Luhn-valid card number into `tmp_path` — never into the repository — and asserts
the scan fails on each. All synthetic values are assembled at run time, because the test
module is itself inside the scanned tree; the real-tree test would otherwise catch the
test file. A companion receipt (`privacy-fixture.json`) records the failing run, and the
workflow re-runs the fixture tests in CI so the gate cannot silently lose sensitivity.

Real tree: **PASS** — 1,522 files (1,479 text, 43 OOXML/PDF containers), 0 findings,
0 exemptions, 98 files listed without text coverage and every one of them an opaque or
compressed payload. The counts move as other agents add files; `privacy-gate.json` is the
authoritative receipt for the run.

## Borrowed from `edithatogo/careops-rims`

Read-only inspection of that sibling's `privacy.yml` and `.careops-security/check.py`
contributed four ideas: findings carry **rule and path but never matched text**, because
the receipt is itself published; exemptions are **explicit, written and digest-pinned in
spirit**; opaque binaries are **enumerated rather than silently skipped**; and the job is
`contents: read`, SHA-pinned, explicitly timed out, with no bypass. This repository
deliberately does **not** copy the sibling's git-history and index-based scanning or its
reviewed-artifact approval file, for the reasons in the limits below.

## Documented limits — what this gate does not cover

1. **Personal names are not detected**, in free text or in document metadata. `dc:creator`
   and `cp:lastModifiedBy` in the tracked OOXML files carry author names today. Detecting
   names needs a model plus a name gazetteer; it is out of scope by design, and no claim
   here should be read as covering it.
2. **Free-text addresses, postcodes and dates of birth** are not detected outside a named
   field.
3. **Opaque payloads** (98 files: `.npz`, `.png`, `.zip` inside `.vsix`) are listed in the
   receipt, not read; nothing inside a compressed image stream is inspected. Text files
   are read up to 32 MB and containers up to 64 MB, with each container part capped at
   2 MB; nothing in the current tree exceeds either bound, so no file is skipped for size
   today. A file added above the bound would appear in the receipt as `oversize`.
4. **Git history is not scanned.** The gate reads the current working tree only. An
   identifier committed and later removed remains in history; `gitleaks` history covers
   secrets there, not identifiers. A history scan needs a git-based variant, and it is
   recorded as an open gate rather than implied.
5. **Scope is a working-tree walk**, pruned by the local scopes of `.gitignore` and by
   declared submodule paths, not `git ls-files`. A file that is ignored but present
   locally is not scanned, and the declared submodule (`extensions/conductor`) belongs to
   a different repository.
6. A clean run is **evidence, not a proof**: the gate can only report the shapes it knows.

## Open gates and the next executable command

- **History scan for identifiers** — not implemented; next executable command:
  `git rev-list --objects --all | git cat-file --batch` piped through the same value
  rules in a `--history` mode, to be reviewed before it is claimed.
- **Name and address detection** — deliberately out of scope; requires a model.
- **Whole-profile acceptance** — this task ran the scoped checks below; the full profile
  with a fresh covered suite and the artifact re-seal is the parent's step, and no hosted
  run is claimed here.

## Verification executed for this task

```
uv run --frozen --no-sync python -m ruff check quality tests
    -> All checks passed!                                        (exit 0)
uv run --frozen --no-sync python -m ruff format --check quality tests
    -> 74 files already formatted                                (exit 0)
uv run --frozen --no-sync python -m ty check --error-on-warning
    -> All checks passed!                                        (exit 0)
uv run --frozen --no-sync python -m basedpyright
    -> 0 errors, 0 warnings, 0 notes                             (exit 0)
uv run --frozen --no-sync python -m pytest -q -p no:cacheprovider
    -> 1078 passed in 20.73s                                     (exit 0)
uv run --frozen --no-sync python -m quality.hooks workflow .github/workflows/privacy.yml
    -> zizmor: No findings to report. Good job!                   (exit 0)
uv run --frozen --no-sync python -m quality.privacy
    -> Scanned 1522 files (1479 text, 43 containers); 0 finding(s);
       98 file(s) without text coverage                          (exit 0)
uv run --frozen --no-sync python -m quality.privacy --root <fixture>
    -> 9 finding(s); exit 1, receipt privacy-fixture.json
actionlint (whole workflow directory)                            (exit 0)
zizmor --offline --persona=pedantic .github/workflows   -> 0 findings (1 pre-existing ignore)
uv run --frozen --no-sync python -m quality.cli --profile quick
    -> pytest, inputs, context all PASSED                        (exit 0)
```

A mid-session full-suite run reported one failure in another agent's
`tests/test_doctest_examples.py::test_importable_modules_run_their_examples[quality.contracts]`
while that file was being edited; it neither reproduced on a re-run nor touched this
module. It is reported here, not fixed here.
