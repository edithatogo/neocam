# Execution ledger — v14-02 acceptance integrity

2.1 Source-register reconciliation — DONE (2026-10-31).
- Reproduced: `python -m quality.source_archive --output verification/v7/source_archive.json`
  failed with `Source size mismatch` and `Source digest mismatch` for
  `sources/retrieve_originals.py`, because `sources/manifest.json` pins the retrieval
  tool's own bytes.
- Evidence preserved: the burn-down audit proved the cleaning was behaviour-preserving
  (AST comparison identical after reconciling declared edits; stdout byte-identical,
  sha 27f4e7d7…, 555 bytes).
- Fix: the register record for `sources/retrieve_originals.py` now carries the cleaned
  file's size and digest (2,464 → 5,425 bytes). No other field changed.
  `quality.source_archive` now verifies clean.
- Ordering rule (to be recorded in the runbook by task 2.1.e): the artifact re-seal must
  be the LAST mutation before acceptance, because both the source register and the
  artifact manifests pin calculation inputs. A mid-wave seal is invalidated by any later
  edit — which is exactly what happened when the strictness and mutation work landed
  after the earlier re-seal.

2.2 Full-profile green and hosted evidence — PENDING. Last measured full profile:
29 passed / 2 failed (`current_release` stale seal, `source_integrity` register
mismatch). `source_integrity` is now fixed; `current_release` requires the final re-seal
immediately before the acceptance run.
