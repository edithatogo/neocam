# Experimental / bleeding-edge feature trials — measured baselines (2026-10-31)

Task 1.4 of `v14-01-engineering-rigour` requires a measured baseline before any trial is
adopted, and a revert with evidence if a trial does not pay for itself. This file records
the measurements taken before the trials were applied.

## 1. `COVERAGE_CORE=sysmon` (experimental `sys.monitoring` tracer) — ADOPT

| Core | Wall time (suite) | Coverage | Missed lines | Partial branches |
|---|---|---|---|---|
| default (`ctrace`) | 6.53 s | 94.17% | 153 | 36 |
| `sysmon` | **6.06 s** | 94.17% | 153 | 36 |

~7% faster with byte-identical coverage, so it is a strict improvement rather than a
trade. Contingency: unset the variable; nothing else depends on it. Second-order benefit
worth measuring later: pytest-gremlins uses a coverage pre-scan for test selection, where
a faster core could trim the ~7-minute mutation step — not yet A/B measured.

## 2. `uv pip check` (environment integrity) — ADOPT as a cheap gate

```
Checked 74 packages in 4ms
All installed packages are compatible
```

The specific failure it covers: a broken or mismatched installed environment (a
half-synced venv after an interrupted `uv sync`, or a version present that the lock does
not resolve) currently surfaces as confusing test/typing errors rather than as one clear
gate failure. Cost: 4 ms.

## 3. `uv export --frozen` — AVAILABLE, not adopted yet

Produces a deterministic 180-line requirements view for the assurance +
tabular + research + reporting set. The repository already emits a cyclonedx SBOM via
pip-audit, so this would be a second dependency-listing artefact unless an external
consumer needs a plain requirements file. Verdict: record as available; adopt only when
a concrete consumer exists (avoids a duplicate camp).

## 4. `pip-audit --vulnerability-service=osv` — SKIP (no measured benefit)

| Service | Packages scanned | Vulnerabilities |
|---|---|---|
| default (PyPI advisory DB) | 74 | 0 |
| `osv` | 74 | 0 |

Identical results, so there is no evidence to justify the change today. Contingency:
revisit if a PyPI-advisory miss is ever observed; OSV covers ecosystems this project does
not use.

## 5. `matplotlib.typing` — PENDING (real gap, blocked only by file ownership)

`matplotlib.typing.ColorType` exists in the installed 3.11.2. Roughly seven
`reportUnknownMemberType` suppressions exist at matplotlib call sites because its stubs
end in unannotated `**kwargs`. Replacing those suppressions with real types is a genuine
"top of scope" improvement; scheduled in the scripts pass rather than duplicating work
while another agent owns `scripts/`.

## 6. pytest-gremlins `--gremlin-batch` — REJECT (measured worse)

A/B on the same target (`src/sensitivity.py`, same operators, 2 workers):

| Mode | Wall time | Zapped | Survived |
|---|---|---|---|
| default (per-mutant) | **42.2 s** | 78 (99%) | 1 |
| `--gremlin-batch --gremlin-batch-size=10` | **175.0 s** | 75 (95%) | 1 |

Batching was **4× slower** here and reported *fewer* mutants (76 vs 79 accounted for), so it
both costs time and distorts the summary the gate reconciles. Rejected; the default
per-mutant execution stays.

Related finding: **sharding the mutation run across CI jobs is not viable as things stand.**
`quality.checks mutation` reconciles a single summary (`total = zapped + survived +
timeout + error + pardoned`) from one report file, so several partial reports cannot be
combined into that gate without a merge step that pytest-gremlins does not provide. The
mutation step therefore stays a single ~7-minute job, and any future speed-up must keep
one reconcilable report.

## 7. Scheduled, not yet measured

- hypothesis `target()`/`event()` plus a seeded non-derandomised CI profile (the current
  `panda_ci` profile sets `derandomize=True`, which stops the suite exploring new
  examples, and `deadline=None`, which disables a check).
- pytest-gremlins batching/sharding for the 7-minute mutation step.
- scipy `qmc.Sobol(optimization=...)` and `sklearn.frozen.FrozenEstimator` (verified
  available) — legacy-analysis script only, no evidence of need yet.

## Dependency-weight finding for the task 1.5 spike

`pydantic` (2.x, with `pydantic-core`) is **already installed transitively** — it arrives
via `scalene`. `uv export` shows it as an indirect requirement, and the resolved lock has
never declared it directly.

- Option A — adopt pydantic for harness validation: adds **no** new resolved package, and
  brings settings/validators/JSON-schema support.
- Option B — msgspec: a genuinely new package (small, zero-dependency, very fast).
- Tradeoff worth stating plainly: option A would make the harness depend on a library
  that only exists because a profiler needs it, so removing or repinning scalene could
  silently remove the harness's validation engine. Option B keeps that coupling out of
  the tree at the cost of one small new package.

The spike (task 1.5) must weigh that coupling, the LOC removed, and the fact that the
suite asserts exact validation messages.
