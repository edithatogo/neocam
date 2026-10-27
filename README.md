# Panda Vision: preliminary economic evaluation v2

Current deliverables are in `outputs/v2/`. Earlier v1 outputs/history are preserved but superseded.

## Decision and evidence boundary
Video-supported versus telephone-supported neonatal consultation. No prospective recruitment or structured expert elicitation is required. The local pilot forecast is 10–15 consultations **per site** annually. The 2022 Queensland births roster is historical; current site capability and private-site detail are not certified. All clinical effects, geographic priors and marginal resource assumptions remain labelled.

## Run the numerical model
The available environment tested Python 3.13.5, NumPy 2.3.5, pytest 9.0.2 and coverage 7.13.3. `requirements-tested-snapshot.txt` records it. `requirements-latest.in` specifies independently checked newer targets but is **not a resolved transitive lock**.

```sh
python -m pytest -q
python scripts/verify.py
python scripts/run_v2.py
```

Change `data/parameters.json` to change the model. Model run output preserves parameter/source hashes. The Excel workbook recalculates the deterministic pilot; its state and PSA tabs are snapshots requiring a Python rerun.

## Authoring
`build_reports_v2.py` generates figures and DOCX using matplotlib/python-docx. `build_workbook_v2.py` uses the provided artifact_tool authoring environment, not an ordinary open-source pip dependency. `build_slides_v2.js` uses PptxGenJS and the host's slide QA helpers. Numerical model execution is independent of these authoring utilities. Document regeneration requires these authoring capabilities and the supplied corporate assets. The rendered outputs are supplied; no claim of standalone artifact rendering in CI is made.

## Assurance
75 local tests passed; v2 model branch-inclusive coverage 96%. Data/source contracts and fixed-seed reproducibility passed. A regression gate prevents partial model receipts from being labelled full release assurance. Official GitHub Actions are SHA-pinned with read-only permissions, Python matrix, lint/property/coverage/audit stages and a non-publishing release gate.

**Blocked/unexecuted:** latest dependency resolution, Ruff/Hypothesis/ty/pip-audit, hosted Actions, newer Python matrix, and actual Conductor submodule checkout. Network DNS prevented installation. See `verification/assurance.json`, failure receipts and `outputs/v2/Panda_Vision_verification_v2.md`. No GitHub remote deployment or production-readiness claim.

## Context and submodule
Start with `AGENTS.md` and `conductor/current-state.json`. The Conductor gitlink is pinned, but its working tree is absent. In a connected authorised checkout:

```sh
git submodule update --init --recursive
```

Retain the exact pin until deliberately reviewed. Do not publish CHHHS corporate templates or internal material through an automatic workflow. Clinical software, device approval and procurement are outside this model's authority.
