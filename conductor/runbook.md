# Current v5 entrypoint

Read `conductor/current-state.json`, then the relevant active track only. Exact analysis: `OPENBLAS_NUM_THREADS=1 OMP_NUM_THREADS=1 MKL_NUM_THREADS=1 python scripts/analyse_v5.py`. Do not change original scientific parameters merely to obtain a preferred option. Reference equal video effects are hypothetical. Keep new procurement, existing capital and shared allocation distinct.

Run `python -m quality.cli --profile full` for acceptance. Current receipts go to `verification/v5`; the ordinary suite runs once under coverage. Optional research targets are checked but not installed in this host; actual analysis versions are in results_v5.json. Missing tools, missing lock or unpopulated submodule cannot be passed. Existing source/plots and prototype assumptions are not clinical validation.

Journal strategy: `docs/publication_strategy_v5.md`. Corporate template assets and the ELC pack must not be published without redistribution permission. Do not submit to a journal or publish a repository without author approval.

## Retained v4 runbook (historical profile paths are superseded above)

# Single-developer runbook — v4

## Authority and scope
Read `current-state.json`, the active track and `.agents/skills/maintaining-lean-ci/SKILL.md`. Explicit user instructions and source/parameter registers control the work. Engineering v4 adds no clinical parameter. The economic specification remains v2/v3, rerun into `outputs/v4`; diagnostics use existing parameters. Source checks establish consistency, not empirical truth of estimated effects/costs.

## Environments: pin, resolve, review, then freeze
`pyproject.toml` controls Python pins. `quality/native-tools.json` controls checksum-pinned native tools. Polars is the sole DataFrame engine; NumPy/CSV remain appropriate for this small model. Do not install pandas/xarray or Hypothesis extras that introduce them.

The current runtime cannot download packages. No real `uv.lock` exists. On a connected authorised checkout:

```bash
python -m pip install uv==0.13.6
uv lock --upgrade
python -m quality.checks lock
# Review lock and compatibility; commit the actual resolved lock before normal CI.
uv sync --frozen --group assurance --extra tabular
uv run --frozen --no-sync python -m quality.bootstrap
git submodule update --init --recursive
uv run --frozen --no-sync python -m quality.cli --profile full
```

Normal CI executes `uv lock --check` before `uv sync --frozen`. Pins/configuration are not successful installation. Resolve conflicts explicitly; do not fabricate lock hashes, silently downgrade, or suppress whole families of diagnostics. Hosted CI is unexecuted until an actual exact-commit run passes.

## Execution scopes
- **Edit loop:** `python -m quality.cli --profile quick`. Complete ordinary tests plus input/context checks; no release claim.
- **Hooks:** `uv run --frozen --no-sync prek install`; thin hooks call canonical tool configuration. No mutation/profiling in every commit. Installation not performed here.
- **Optional local selection:** install the feedback group in a controlled environment, then `python -m quality.feedback --mode tests`. Testmon absence falls back to all ordinary tests, not a selection-speed claim.
- **Optional local mutation:** `python -m quality.feedback --mode mutation`. Gremlins absence is blocked. Valid incremental caches are local-only; source/data/config/dependency/interpreter/test changes invalidate evidence.
- **PR:** `python -m quality.cli --profile pr`. One covered ordinary suite, complete relevant static/security/input checks. Coverage report reuses the same execution.
- **Full acceptance:** `python -m quality.cli --profile full`. All mandatory gates, clean mutation evidence, exact installed versions, real lock, native binary integrity, profiling and tabular reconciliation. Every required gate must pass.

Keep serial testing until measured xdist benefit is established. Testmon and xdist remain optional and unbenchmarked here. Cache downloaded artifacts, not whole environments or acceptance receipts. Cancel obsolete PR jobs, not full acceptance. One reviewed Renovate configuration replaces the duplicate updater; bot activation is not claimed.

## Verification policy
Coverage: 90% scoped model/harness and 95% active numerical module. Mutation: nonzero mutants, at least90% killed, no unexplained timeout/error/pardon. These thresholds are unchanged. Ruff selects ALL/preview with formatter-conflict exemptions only. ty/basedpyright retain strict configurations. Scalene uses reproducible CPU/memory workloads without code upload. Gitleaks logs are redacted; Vale uses local styles; actionlint and zizmor inspect CI itself.

Receipts contain actual commands, exit status, source/input fingerprints, elapsed times and log hashes. Blocked is not passed. Source changes invalidate old receipts. The portable skill checker tests receipt consistency, not cryptographic authenticity or hosted execution.

## Analysis and artifacts
```bash
python scripts/run_v2.py --out outputs/v4 --iterations 20000
python scripts/complete_analysis_v4.py
python scripts/build_documents_v4.py
node scripts/build_slides_v4.js
# Workbook authoring uses artifact_tool, outside the numerical model environment:
python scripts/build_workbook_v4.py
```

Authoring requires the recorded document/plot/office-tool environment. Do not silently add those tools to runtime dependencies. Render the two-page plan and supplement, inspect charts/tables and slides, verify workbook formulas and preserve the actual output manifest. Full CSV/PNG/SVG data live in `outputs/v4`. Re-running analysis must precede relabelling artifacts.

## Handoff and remaining gates
Commit bounded changes, update Conductor implementation/acceptance separately, and deliver a versioned ZIP plus Git bundle. Restore the bundle and rerun tests. No remote push, app installation or publication follows from a local archive.

Current limits: external tools unavailable, missing real lock, Conductor gitlink not populated, no hosted CI, no independent agent pressure test, historical population/effect/cost uncertainty and unverified QEP. Read the current receipt rather than inheriting a previous pass. Combined repeated benchmark drivers were interrupted by the sandbox; single-command timings are reported with their narrower scope.
