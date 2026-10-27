# Panda Vision evaluation — v3 engineering assurance

This branch refines the existing model and verification workflow. It does not add economic parameters, clinical features or a new modelling framework. Numerical and evidence assumptions remain those of v2; earlier rendered economic deliverables remain in `outputs/v2/`.

## Start here

Read `AGENTS.md`, then [the single-developer runbook](conductor/runbook.md), [current state](conductor/current-state.json) and [tracks](conductor/tracks.md). The runbook owns environment setup and acceptance commands; do not maintain competing copies of those instructions.

```bash
python -m quality.cli --profile quick
```

The quick profile runs the ordinary test suite and input/context checks. It never implies full assurance. The full profile also requires Ruff, ty, basedpyright, Hypothesis, pytest-gremlins, Scalene, Gitleaks, Vale, exact installed dependency versions, a reviewed hash lock, security audit/SBOM, Polars reconciliation and the actual pinned Conductor checkout.

## What is verified

`verification/v3/` contains the baseline, deliberately failing regression tests, subsequent passing tests, coverage, source-input hashes, model-output parity and actual command receipts. The numerical repairs address ignored PSA odds-ratio overrides, lost birth-year metadata, malformed input acceptance and near-zero discount instability.

All 27 parameter values and nine protected data/evidence files remain unchanged. Five default deterministic portfolios and pilot/statewide-spoke 20,000-draw PSA cohorts match the baseline within the declared floating-point tolerance. The source register is reconciled, not converted into proof of assumed clinical effects or local costs.

## What is not verified

The environment cannot download the declared newer packages or native tools. No real `uv.lock` has been generated. Requested external linter, type, generative, mutation, profiler, security and prose checks remain unexecuted, and full assurance intentionally returns nonzero. Configuration is not a passing tool result; a first connected run may expose diagnostics requiring repair. Hosted GitHub Actions and the Python-version matrix have not run.

The available host uses Python 3.13.5, NumPy 2.3.5, pytest 9.0.2 and coverage 7.13.3. The target stack and primary source links are in `evidence/dependency_targets_v3.json`. Do not claim these targets are installed or compatible until frozen-install and full receipts verify them.

## Small model, explicit boundaries

NumPy remains the numerical dependency. The small source tables use standard-library CSV; Polars is the only permitted DataFrame library, provided as a tabular verification extra. Direct imports and resolved project dependencies are checked for pandas/xarray. Their absence from a future resolved environment cannot be certified before the real lock exists. Do not import the pandas-backed portions of an external library to bypass this policy.

`python scripts/run_v2.py` reruns the existing economic analyses. Excel deterministic formula cells recalculate locally; statewide/PSA tabs are snapshots requiring a model rerun. The 2022 birth roster is historical; current facility capability, geographic transport mix, clinical effects, current QEP and marginal retrieval costs retain their documented limitations.

## Historical report generation

The prior report builders use the supplied corporate templates and a host authoring environment: matplotlib/python-docx, artifact_tool, and PptxGenJS/slide helpers. These are not dependencies of the model or new assurance environment. This engineering pass has not rebuilt or certified that authoring stack. Preserve the supplied v2 Word/PDF/Excel/PowerPoint outputs rather than implying they were newly rendered.

## Git and privacy

The branch is `conductor/panda-vision-v3-assurance`. The Conductor submodule gitlink is pinned, but its working-tree checkout remains blocked by DNS. A gitlink alone is not an installed Conductor runtime. No repository was created, pushed or published. The release workflow verifies only; it does not deploy or publish corporate templates, internal papers or patient information.
