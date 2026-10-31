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

## Additional gate-stability work landed in this track's window (2026-10-31)

- `tmp_path_retention_policy = "none"` in `[tool.pytest.ini_options]`. Reason: pytest's
  numbered tmp directories are swept on exit, and under the mutation gate's two workers
  that cleanup raced (an unclosed-scandir ResourceWarning escalated by
  `filterwarnings = ["error"]`, plus an `rm_rf` race), producing spurious `Error` mutants.
  The mutation gate treats **any** error as a failure regardless of score, so this was a
  real gate-fragility risk rather than cosmetics. Nothing in the suite inspects a previous
  run's tmp directories. Verified: scoped gremlins run at `error: 0`, `timeout: 0`.
- `quality.feedback` incremental path repaired: the plugin was invoked as
  `-p testmon.pytest_testmon`, which collides with pytest-testmon's own entry-point name
  (exit 3), and the sys.monitoring core aborts testmon's `switch_context()` under
  `filterwarnings = ["error"]`. Fixed to `-p pytest-testmon` with a scoped
  `COVERAGE_CORE=ctrace` override for that path only. Two contract tests that had enshrined
  the broken invocation were corrected (not weakened).
- Privacy gate performance: `quality/privacy.py` scanned the tree in ~15 s with
  `_inspect_line` called 1.22 million times (five regex passes per line). Because gremlins
  runs the suite once per mutant, an optimisation is required and is in progress with an
  equivalence proof (identical findings and skip semantics).

These three items are prerequisites for a full-profile run that is genuinely green, not
merely green because a gate happened not to exercise them.

