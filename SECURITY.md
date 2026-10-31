# Security policy

Panda Vision is a single-maintainer health-economics research repository. It runs no
service, endpoint or hosted application: the "attack surface" is the repository, its
GitHub Actions workflows and the artefacts published from them. This policy is written
to match that reality and makes no claim of a security team, an inbox, a bug bounty or
a response deadline.

## Supported versions

- Python **3.15** only. `pyproject.toml` (`requires-python`) and `uv.lock` are the
  single source of resolved versions; there is no version matrix.
- The **current default branch** only. Older commits, tags and feature branches are
  retained for provenance but are not maintained or patched.

## Reporting a vulnerability

Use GitHub's **private security advisories** on this repository
(Security → Advisories → "Report a vulnerability"). That channel is private, so a
report stays confidential until it is triaged or disclosed.

Please do not open a public issue for a suspected vulnerability. This is a
best-effort, single-maintainer project: reports are handled as time allows, with no
guaranteed acknowledgement, fix window or severity SLA. There is no bug bounty.

## In scope

- The repository's source, configuration and documentation.
- GitHub Actions workflows under `.github/workflows/` and their third-party runners.
- The build/publish supply chain: pinned actions, `uv.lock`, and the assurance gates
  in `quality/cli.py`.
- Published artefacts: anything under `outputs/`, `evidence/`, `verification/` and
  `docs/`.

## Out of scope

- Clinical, epidemiological or policy **claims and interpretation**. This repository
  models scenarios; it is not a clinical decision tool and its outputs are not
  clinical advice.
- Model **limitations, assumptions and parameter uncertainty** (see
  `conductor/current-state.json` `known_limitations`). Disagreement with a finding is
  a research question, not a vulnerability.
- Anything requiring the maintainer's private credentials or accounts.

## Safeguards in place

- **Secret scanning locally:** gitleaks runs at commit and push time via
  `.pre-commit-config.yaml`, backed by `.gitleaks.toml` with no allowlists. The
  assurance gate scans both working tree and full history (`gitleaks_tree`,
  `gitleaks_history`).
- **Secret scanning on GitHub:** secret scanning and push protection are enabled on
  the public repository.
- **Dependency risk:** Renovate is the only dependency bot (`renovate.json`,
  `automerge: false`), with Dependabot vulnerability alerts and automated security
  fixes enabled on GitHub. No `.github/dependabot.yml` exists by design
  (`tests/test_v4_config.py`).
- **Supply-chain pinning:** every GitHub Action is pinned by commit SHA and kept
  SHA-pinned by Renovate `pinDigests`; `uv.lock` pins resolved versions and CI runs
  `uv lock --check` before `uv sync --frozen`.
- **Least privilege:** workflows declare `permissions: contents: read` and
  `persist-credentials: false`.
- **Vulnerability and inventory gates:** `pip_audit` and `sbom` (CycloneDX) run in the
  full assurance profile.
- **Provenance:** signed/attested build provenance is **not** currently configured;
  the release workflow (`release-gate.yml`) publishes no artefact and performs no
  deployment.

See `docs/security-automation.md` for what is automated and what is deliberately not.
