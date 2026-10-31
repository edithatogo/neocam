# v14 design authority — engineering rigour, acceptance integrity and ecosystem integration

Date: 2026-10-31. Owner decisions supersede earlier drafts in this file.
Status: implementation begun; external acceptance remains a separate gate.

This document is the design authority for the v14 tracks. It records the measured
dependency audit, the "foot in two camps" findings with options and tradeoffs, and the
decisions taken, so later work does not have to re-derive them.

## Owner decisions already taken

1. **One interpreter.** Python 3.15 only (`requires-python >=3.15,<3.16`); no 3.13/3.14
   support. Implemented and verified (`verification/v13/burndown/python-policy.md`).
2. **Maximal strictness.** ruff `select = ["ALL"]` + preview; ty `all = "error"` plus
   `--error-on-warning`; basedpyright `all` + experimental features + blanket
   `# type: ignore` banned + ignore auditing; pytest strict markers/config,
   warnings-as-errors and `xfail_strict`. Implemented.
3. **Bleeding-edge CI/security.** SHA-pinned actions, harden-runner, CodeQL,
   dependency-review, OpenSSF Scorecard, SLSA-style evidence attestation, hardened
   Renovate, `SECURITY.md`, `.gitignore` leak vectors. Implemented.
4. **reportlab is incorporated, not removed.** It must do real work in the document
   pipeline (track `v14-01`, task 1.1) rather than sit declared-but-unused.

## Dependency audit (measured 2026-10-31, installed versions)

| Dependency | Actual use | Verdict |
|---|---|---|
| numpy 2.5.4 | 46 files; `default_rng`/`Generator`, `numpy.typing.NDArray`, no deprecated aliases | at top of scope |
| polars 2.1.0 | independent reconciliation probe (rows/sum/nulls/duplicates) + gate | deliberate second engine |
| python-docx 1.2.0 | 7 files; private `_element`/`_p` OOXML handles (11 justified ignores) | private API is unavoidable today |
| python-pptx 1.0.2 | 1 file | fine |
| reportlab 5.1.0 | **zero imports before this track** | to be incorporated (task 1.1) |
| matplotlib 3.11.2 | 7 files; `matplotlib.typing.ColorType` available but unused; ~7 suppressions from untyped `**kwargs` | fixable gap (task 1.4) |
| scipy 1.18.1 | only `scripts/analyse_v5.py`; Sobol `random_base2` + `optimization=` available | historical analysis only |
| scikit-learn 1.9.1 | same legacy script; `FrozenEstimator`, `set_config` unused | historical analysis only |
| hypothesis 6.170.14 | one file; `max_examples=100, deadline=None, derandomize=True`; no `target()`/`event()` | gap: `deadline=None` disables a check; `derandomize=True` stops exploring new examples |
| coverage 7.17.0 | branch, fail-under 90 (+95 core) | `COVERAGE_CORE=sysmon` available, unused |
| pip-audit 2.10.1 | `--local` json + cyclonedx SBOM | `--vulnerability-service=osv` available, unused |
| uv 0.13.6 | `lock --check`, `sync --frozen`, `run --no-sync` | `uv pip check`, `uv export`, `uv python pin` unused |
| pytest-gremlins 1.13.1 | 5 operators, `max_pardons=0`, 2 workers, acceptance cache off | batching/sharding available for speed |
| ty, basedpyright, ruff, scalene, testmon, xdist, prek, zizmor | at their maximum strictness settings | fine |

## "Foot in two camps" decisions

### D1 — reportlab (owner decision: incorporate)
- Task 1.1: reportlab must produce a real artefact with a test and a receipt, and must
  not duplicate the matplotlib PDF path. Intended use: a paginated PDF document (the
  decision memo / plan) where ReportLab's text flow and page furniture are genuinely
  better than a figure-based PDF.
- Contingency: if the artefact duplicates an existing DOCX with no added value, the
  track records that finding and the dependency returns to the audit list rather than
  being silently kept.

### D2 — ty + basedpyright (recommendation: keep both)
- Options: (a) keep both; (b) basedpyright only; (c) ty only; (d) ty in hooks,
  basedpyright in the gate.
- Rationale: they found different defects on this codebase — basedpyright found breadth
  (`reportAny`, partially-unknown types), ty found `invalid-assignment`,
  `redundant-cast`, `unsound-assignment`. That is independent signal, not duplication.
- Tradeoff: ~86 suppression comments and two gate runtimes.
- Decision: (a) keep both; the division of labour is recorded here. Contingency (d) if
  cost outweighs value.

### D3 — scipy + scikit-learn scope
- Finding: they are used only by the historical `scripts/analyse_v5.py`; the model
  (`src/sensitivity.py`) is numpy-only.
- Decision: keep, documented as historical-analysis tooling; the runbook states the
  model itself needs numpy only.

### D4 — performance tooling
- Decision: do **not** add `pytest-benchmark`; scalene (gate) plus the bespoke
  benchmark module remain the single performance camp. Contingency: adopt
  pytest-benchmark only if the bespoke module is retired in the same change.

### D5 — secret scanning depth
- Decision: do **not** add trufflehog. gitleaks (commit + push) and GitHub push
  protection already cover pattern matching and server-side blocking; trufflehog's
  unique value (verifying live credentials) does not apply to this repository.

### Deliberate non-violations (do not "fix" later)
polars reconciles the source table independently of the model's numpy path; actionlint
(syntax) and zizmor (security audits) are complementary; hypothesis (property) and
gremlins (mutation) are different; testmon and xdist are routed per mode because they
conflict; coverage is used directly (no pytest-cov).

## Track map

| Track | Scope |
|---|---|
| `v14-01-engineering-rigour` | reportlab incorporation, testing depth, static-analysis depth, custom-validation replacement spike, experimental feature trials |
| `v14-02-acceptance-integrity` | source-register and artifact-manifest governance (including the re-seal-last rule), full-profile green, hosted CI evidence |
| `v14-03-ecosystem-integration` | sibling-repository incorporation: provenance, privacy patterns, citation verification, CI alignment |

## Boundary

No clinical parameter, model behaviour, published number or output path changes in v14.
The clinical/evidence/publication gates in `conductor/blockers-v13.json` remain open and
are unaffected. Frameworks are not added to the model: any dependency replacing custom
code must be justified per-agreement, measured, and confined to the harness (task 1.5).

## Sibling-repository inventory (task 3.1)

Enumeration on 2026-10-31, read-only, through the GitHub REST API for `edithatogo`.
The host `gh` client is authenticated only to `nswhealth.ghe.com`, so github.com was
reached unauthenticated and **208 public repositories** were visible (101 third-party
forks, 107 author-owned). No private repository is visible without a token, so a private
sibling is absent from this inventory rather than inferred, and the owner's "~50
repositories" expectation is not confirmed by the measured count. Nothing was cloned,
installed, executed or imported. Every SHA below was resolved for that repository at
enumeration time; no SHA is reused from another entry, and a recorded pin is never
presented as a head.

Classification: **direct** = materially relevant to this model's subject or toolchain;
**adjacent** = same domain, no concrete integration; **unrelated** = omitted (count at the
end). Available forms: pinned submodule, documented reference, real dependency (imported by
code), reused CI pattern, evidence source. No form is adopted here: the owner picks in one
pass from the decision table.

### Direct siblings

**`edithatogo/neocam`** — this repository, the model itself.
Checked commit `d7e438a098a5c8b5f4c8a86bd68836228c1efa5b` (remote default-branch head at
enumeration). Form: itself. *Not claimed:* that the remote head equals the reviewed local
working tree.

**`edithatogo/conductor-next`** — the Conductor implement/review workflow.
Checked commit `137c1e41ff9c1dc75ff277b9582460a0bd8c4768`, which is also the current
default-branch head, so the pin is still at head. Form: **pinned submodule** (already
present as `extensions/conductor`). *Not claimed:* a populated submodule working tree, a
successful Conductor CLI run, or independent review (the reviewer was the same assistant).

**`edithatogo/mchs`** — NWAU/NEP microcosting and activity-based-funding calculator library.
Checked commit `9fc8d0f33df2aabaef8d4a10f25df12d41ff033e` (the existing checked commit,
re-resolved). The default-branch head has since moved to
`f7f9013dd85ea411140be7f3d463806a15922d56`, recorded as information, not as a re-pin. Form:
**documented reference**, optionally consumed across an import/export boundary. *Not
claimed:* 2026/NEP26 calculator parity (upstream marks it NOT YET VALIDATED), QWAU/QEP
certification, any execution, any code copied into this model, or its pandas runtime
imported. Existing stance preserved and extended.

**`edithatogo/microcosting_healthworkforce`** — rate conversion, indexation and
deterministic-sensitivity microcosting patterns.
Checked commit `dd61438f15db91a0cb51e403f9ec137c7e589b2d` (current default-branch head).
Form: **documented reference** (methods only). *Not claimed:* no rate is imported and no
official current salary value is taken from it, and it was not executed. Existing stance
("methods inform cost components, not official current salary values") preserved.

**`edithatogo/vop_poc_nz`** — value-of-perspective proof of concept for Aotearoa New
Zealand, carrying the fixed-decision perspective contract.
Checked commit `ad84d3090a2d97f2805a86e94a7b9614a3d1ab14` (the inspected commit, and still
the current default-branch head). Form: **documented reference**; its small tie-aware
expected-value contract is reimplemented locally (extract at
`sources/extracts/vop_method_contract.md`). *Not claimed:* the upstream package was not
imported wholesale, its wider VoI machinery was not inspected for parity, and only the
fixed-decision contract is matched. Existing stance preserved.

**`edithatogo/voiage`** — the owner's value-of-information engine (EVPI/EVPPI/EVSI), Rust
core with Python, R and Julia interfaces.
Checked commit `961b982a40c303588d2bcb7d8c5eca2b07ba9be2` (current default-branch head). Form
now: **documented reference, deferred**; a pinned engine would only follow an authorised
task 3.4. *Not claimed:* this model's EVPI is explicitly cost-only and is not `voiage`'s;
no VoI integration was performed; it is not required for the base model. Existing deferral
preserved and gated (below).

**`edithatogo/reimbursement-atlas`** — context-driven reimbursement atlas: source
contracts, evidence readiness and automation scaffolding.
Checked commit `a93516ed416118bc51c1db2b71ab540fa4d0fe52` (current default-branch head).
Form: **documented reference** for reusable provenance, already recorded in the workbook
reference set (`scripts/build_workbook.py`, entry `G2`). *Not claimed:* no turnkey NWAU
engine was found in it, and nothing was imported. Existing stance preserved.

**`edithatogo/template-solo-data`** — solo-maintainer reproducible data pipeline with
reusable CI, Renovate and Codecov OIDC.
Checked commit `4abb00d24ec2738da7b23dfb2c6e5eeaf03bed97` (current default-branch head).
Form: **reused CI pattern** (task 3.3), adopted item by item only where strictly better.
*Not claimed:* no pattern is adopted yet, nothing is adopted for consistency, and this
repository's stricter bespoke gates are preserved rather than replaced.

**`edithatogo/careops-rims`** — sanitised RIMS source templates with secret and privacy
safeguards (the real `privacy.yml`); no operational data.
Checked commit `8fdc68f09a2bdbb9dc1ab0bc39743e810fef6714` (current default-branch head).
Form: **reused CI pattern** (task 3.2). *Not claimed:* not executed and not yet
implemented here; no operational or private data is adopted; the check must pass the real
tree and fail a synthetic identifier fixture, and must not weaken gitleaks or push
protection.

**`edithatogo/sourceright`** — reference and citation verification infrastructure for
academic and legal citation workflows.
Checked commit `6e2a69cba6bf65c35bef65c193b3e91b46df5c91` (current default-branch head).
Form: **evidence source** for citation receipts against `sources/` and
`source_register.csv`. *Not claimed:* nothing was run, no existing register entry has been
re-verified by it, and it is a verification tool, not a source of new observations.

**`edithatogo/riopa-infrastructure`** — open, modular, provenance-first infrastructure for
reproducible public-data research.
Checked commit `da1fc847a92cfa5b41e2dae01812554c10eba74e` (current default-branch head).
Form: **documented reference** for provenance patterns. *Not claimed:* this repository's
receipts and manifests are not riopa's, no parity was measured, and patterns are
inspiration rather than an imported mechanism.

### Adjacent siblings (same domain, no concrete integration)

Named so the omission is deliberate, not accidental; none is proposed for incorporation.

- Health economics, funding and policy simulation without an interface to this model:
  `gtpcnz`, `closer-to-whom`, `ee_trd`, `new-drug-reimbursement-game`, `UOGTO`, `nhra_game`,
  `nztaxmicrosim`, `microcosting_genomics`, `lifecourse`, `global-medicines-atlas`,
  `atlas-health-policy-anz`, `rareburden-commons`.
- The `mchs` contract family — wrappers and distribution rather than new capability, so any
  decision belongs with the `mchs` entry: `NwauCore.jl`,
  `NationalWeightedActivityUnitWrapper.jl`, `mchs-swift`, `homebrew-mchs`.
- Research-toolchain siblings overlapping a slot already covered: `repository-standards`
  (same CI/Renovate slot as `template-solo-data`, fold into 3.3), `careops-ppg` (a second
  secret-scanning reference for 3.2), `searchright` and `citeweft` (search and document
  extraction neighbours of `sourceright`), `research-publications`,
  `conductor-upstream-canonical` (upstream of the fork that is pinned).

### Omitted

175 repositories are omitted as unrelated to this model's subject and toolchain: 100
third-party forks (upstream projects tracked for convenience) and 75 author-owned
repositories outside health-economic modelling, provenance or this project's CI. They are
recorded in the enumeration artifact of this task, not here.

### VoI gate

`voiage` and `vop_poc_nz` already run a canonical specialist synchronisation between them —
`.github/workflows/canonical-specialized-voi-sync.yml` in `voiage` and
`specialized-voi-governance-sync.yml` in `vop_poc_nz` — so they are one VoI surface, not two
independent references, and pinning either alone would pin a synchronised pair at a single
point in time.

Alignment of this model's VoI machinery with that surface is **gated** on the owner
confirming that decision utility is credible here. That confirmation is not engineering
work: alignment would change model results, so it cannot be folded into v14-03 and must
become a model track with its own parity suite and explicit disclosure (task 3.4). Until
then the recorded deferral of `voiage` and the cost-only EVPI stance both stand unchanged.

### Decision table

| repo | form | rationale | decision needed |
|---|---|---|---|
| `neocam` | itself | the subject repository | no |
| `conductor-next` | pinned submodule (existing) | implement/review workflow already pinned at `137c1e41` | no |
| `mchs` | documented reference (optional interface) | relevant NWAU library; 2026 parity not validated | no — stance set; only to request the optional interface |
| `microcosting_healthworkforce` | documented reference | cost-component methods, no rates | no — stance set |
| `vop_poc_nz` | documented reference | small fixed-decision contract reimplemented locally | no — stance set |
| `voiage` | documented reference now, pinned engine only if authorised | EVPPI/EVSI engine deferred on credibility | **yes — 3.4 gate** |
| `reimbursement-atlas` | documented reference | reusable provenance; no turnkey NWAU engine | no — stance set |
| `template-solo-data` | reused CI pattern | OIDC/Renovate pattern may be strictly better | **yes — 3.3** |
| `careops-rims` | reused CI pattern | real `privacy.yml` plus privacy/secret safeguards | **yes — 3.2** |
| `sourceright` | evidence source | citation verification for `sources/` receipts | **yes** |
| `riopa-infrastructure` | documented reference | provenance-first infrastructure patterns | **yes** |
