# Security automation inventory

What this repository automates, what each layer actually guarantees, and what it
deliberately leaves to humans. Automation here is a **guardrail, not assurance**: no
gate in this list reviews the clinical, epidemiological or policy meaning of an output.

## Dependency policy

- **Renovate is the only dependency bot.** Config: `renovate.json`; asserted by
  `tests/test_v4_config.py::test_only_one_dependency_bot_and_reviewed_groups`, which
  requires `automerge is False` and at least two `packageRules`, and requires
  `.github/dependabot.yml` to **not** exist.
- `automerge: false` globally; security updates get elevated priority and labels and
  are still human-merged. Numeric/tabular and developer-tool packages are grouped so
  updates arrive as reviewable batches.
- `pinDigests: true` keeps GitHub Actions SHA-pinned; `rangeStrategy: "pin"` matches
  this exact-pinned project; a weekly window, `prConcurrentLimit: 3` and
  `minimumReleaseAge: "3 days"` bound PR volume and new-release exposure.
- Dependabot **vulnerability alerts** and **automated security fixes** are enabled in
  GitHub settings (not a config file).

## Secret-scanning layers

- **Commit/push time:** gitleaks via the local hook config `.pre-commit-config.yaml`
  (`quality.hooks`, kinds `secrets` and `secrets-history`).
- **Assurance gate:** `gitleaks_tree` and `gitleaks_history` in `quality/cli.py`
  (profile `pr`/`full`), using the pinned native binary from
  `quality/native-tools.json`.
- **Ruleset:** `.gitleaks.toml` extends the default ruleset with **no allowlists**;
  `data/`, `outputs/` and `evidence/` stay scanned.
- **Hosted:** GitHub secret scanning and push protection are enabled on the public
  repository.
- **Guarantee:** a clean scan means no *known* rule matched in the scanned range. It
  is not a proof that no secret exists.

## Supply-chain pinning

- Every GitHub Action in `.github/workflows/` is pinned by full commit SHA.
- `uv.lock` pins resolved versions; CI runs `uv lock --check` then
  `uv sync --frozen --group assurance --extra tabular --extra research --extra reporting`.
- Workflows run with `permissions: contents: read` and `persist-credentials: false`.

## Assurance gate list

Profiles are declared once in `quality/cli.py::gates_for_profile`.

- `quick`: `pytest`, `inputs`, `context`.
- `pr`: the fast covered suite.
- `full`: `pytest`, `inputs`, `context`, `current_release`, `source_integrity`,
  `coverage`, `coverage_threshold`, `core_coverage`, `ruff_lint`, `ruff_format`, `ty`,
  `basedpyright`, `hypothesis`, `gremlins`, `mutation_score`, `scalene`,
  `scalene_output`, `gitleaks_history`, `gitleaks_tree`, `vale`,
  `dependency_consistency`, `dependency_lock`, `native_versions`, `locked_versions`,
  `pip_audit`, `sbom`, `conductor_checkout`, `polars_consistency`, `actionlint`,
  `zizmor`, `prek_config`.

What each covers:

| Gate(s) | Coverage |
| --- | --- |
| `pytest`, `coverage*`, `core_coverage` | Tests plus >=90% overall and >=95% on core modules |
| `ruff_lint`, `ruff_format`, `ty`, `basedpyright` | Style and strict typing |
| `hypothesis`, `gremlins`, `mutation_score` | Property and mutation testing |
| `scalene`, `scalene_output` | CPU/memory profiling of the workload |
| `gitleaks_tree`, `gitleaks_history` | Secret scan of tree and full history |
| `pip_audit`, `sbom` | Dependency vulnerability audit and CycloneDX SBOM |
| `dependency_*`, `native_versions`, `locked_versions` | Lock/pin consistency |
| `actionlint`, `zizmor`, `prek_config` | Workflow and hook-config static analysis |
| `inputs`, `context`, `current_release`, `source_integrity`, `conductor_checkout`, `polars_consistency`, `vale` | Repository, provenance and prose checks |

Some gates set `allow_unavailable=True` and are skipped when a tool is absent; a skip
is not a pass. See the runbook's boundaries before citing gate results.

## What is NOT automated

- **Clinical / evidence review.** No gate validates whether a finding is clinically or
  epidemiologically defensible.
- **Independent human review.** Automated checks are author-run; external review is a
  separate, unfilled task (`conductor/current-state.json` `review`).
- **Release authorisation and publication.** `release-gate.yml` runs assurance and
  records a review boundary; it performs no deployment or publication. Publication of
  clinical/evidence claims stays a human decision (`release_ready` remains false).
- **Signed/attested build provenance.** Not configured today.
- **Secret-free guarantee.** gitleaks only reports what its rules match.
