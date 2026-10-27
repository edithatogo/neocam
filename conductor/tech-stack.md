# Technical stack and scope

The active model uses Python and NumPy with standard-library CSV input. Polars is the only permitted DataFrame engine and is an optional independent reconciliation adapter. No pandas/xarray dependency is accepted.

`pyproject.toml` is the direct-pin authority. `evidence/dependency_targets_v3.json` records release verification, not installation. `quality/native-tools.json` records native release digests. A real reviewed `uv.lock` is still required; none is fabricated.

The single local/CI execution authority is `quality/cli.py`, operated through `conductor/runbook.md`. The profile separates fast feedback from expensive mutation/profiling/security acceptance. Tool configuration is in `pyproject.toml`, `.vale.ini`, `.gitleaks.toml` and `.github/workflows/`.

The prior artifact-generation environment and supplied corporate assets are historical, separate from the model. This branch has not rebuilt them or validated their dependency closure.

Conductor's gitlink remains pinned to `137c1e41ff9c1dc75ff277b9582460a0bd8c4768`; actual checkout is blocked. No Conductor CLI invocation is claimed.
