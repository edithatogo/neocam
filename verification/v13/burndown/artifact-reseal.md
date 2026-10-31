# current_release gate: artifact re-seal after the lint/type burn-down (2026-10-31)

## What the gate found

`python -m quality.artifacts verify` (the `current_release` gate) failed after the burn-down
with, for both scopes:

```
{"scope": "outputs/v13-primary",     "errors": ["Calculation dependencies changed"]}
{"scope": "outputs/v13-refinements", "errors": ["Calculation dependencies changed"]}
```

It passed on the previous hosted run (41082033781, commit 4bdb86b), so this is a consequence
of the burn-down having edited `src/`, `scripts/` and `quality/`.

## Why that is expected, and why the re-seal is faithful rather than a rubber stamp

1. **The failure was exclusively about calculation dependencies.** `verify` compares two
   independent things: the digest of every file in the sealed output scopes, and the digest
   of every calculation input (source, data, config, scripts). The pre-reseal run reported
   *only* calculation-dependency errors — it reported **no output digest mismatch**. The
   published artefacts are therefore byte-identical to what was sealed; only the digest of
   the code that would regenerate them moved, because that code was reformatted, annotated
   and had comments/docstrings added. Evidence: `artifacts-verify-before-reseal.json`.

2. **The source changes are behaviour-preserving by independent audit**, not by assertion:
   - numeric-literal AST multisets identical (HEAD vs working tree) across all 41 modified
     files; comparison-operator and boolean-operand profiles unchanged; zero introduced or
     removed `isclose`/`allclose`/`approx`
   - the only two deliberate behaviour changes are the `src/audit_v7.py` RUF069 float-equality
     defect fix and the `TRY004` exception-type fixes, and both carry failing-first tests;
     parity tests (`-k "parity or default or reference"`, 22) and the frozen-input gate
     (`quality.checks inputs`, errors: []) pass
   - generated artefacts were re-rendered and compared byte-for-byte where feasible
     (`build_current_report` md/html identical, PNGs identical)

3. **The re-seal changed only what it should.** Diffing `release_manifest.json` for both
   scopes shows exactly two changed fields and no others:

   | field | before | after |
   |---|---|---|
   | `analysis_inputs` | 26 source digests at `4b2f8825` | the same 26 paths at the new digests |
   | `source_commit_at_generation` | `4b2f8825d67709bc837a087631d9f40ce1aaa351` | `4369f040147d0b566f637fdc44696853cbcb4536` |

   No artifact/output digest changed. Because the output side of the manifest is unchanged,
   this re-seal asserts "these same artefacts correspond to these functionally equivalent
   sources" — it does **not** bless any change in the published numbers.

4. **Post-seal verification passes**: `python -m quality.artifacts verify` → `"errors": []`.
   Seal receipt: `artifacts-reseal.json`.

## What a reviewer should check

- `artifacts-verify-before-reseal.json` contains no output-digest error (proves artefacts
  unchanged).
- The `release_manifest.json` diff contains only `analysis_inputs` and
  `source_commit_at_generation`.
- The two behaviour changes have failing-first tests, and no other semantic change exists
  per the audits listed above.

## Note on the recorded commit

`source_commit_at_generation` records the tip at seal time (`4369f04`), which contains every
source change but necessarily not the manifest update itself (a commit cannot contain its own
hash). The manifest update is committed immediately after, as a receipt-only change.
