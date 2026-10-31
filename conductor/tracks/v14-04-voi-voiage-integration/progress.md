# Execution ledger — v14-04 VoI / voiage integration

Owner direction (2026-10-31): **including `voiage` is the priority**; `vop_poc_nz` is not a
dependency and anything it has that voiage lacks must be integrated **into voiage** as
part of this work. `sourceright` is deferred to the roadmap ("do everything else first").

## Verified facts before implementation

1. **voiage is published and installable in principle.** PyPI `voiage==2.2.0`,
   `requires_python >=3.12`, wheel `voiage-2.2.0-cp312-abi3-macosx_11_0_arm64` plus
   manylinux x86_64 and win_amd64. The **abi3** wheel means the extension is
   stable-ABI compatible with 3.15, and GitHub's x86_64 runners are covered. Apache-2.0.

2. **Hard blocker: voiage cannot install on Python 3.15 today.**
   - voiage 2.2.0 declares `pyarrow>=25.0.0,<26`.
   - pyarrow 25.0.0 and 25.0.1 publish **zero** cp315 wheels (measured across all files).
   - pyarrow 26.0.0 publishes cp315 wheels for macosx_12_0_arm64 and
     manylinux_2_28_x86_64.
   - Consequence: `uv run --with voiage==2.2.0` attempts a pyarrow source build (CMake
     failure), and forcing `pyarrow==26.0.0` is unsatisfiable because the cap excludes it.
   - Therefore task 4.1 (widen the cap upstream) is a prerequisite for this project's
     3.15-only policy; the constraint cannot be overridden honestly from here.

3. **voiage already has a perspective module** — `voiage/methods/perspective.py`
   (665 lines, `METHOD_CONTRACT_VERSION = "1.1.0"`, tie policies first/split/error):
   `Perspective`, `PerspectiveSet`, `ValueOfPerspectiveResult`,
   `value_of_perspective(...)`, `perspective_optimal_strategies(...)`, Pareto helpers, and
   Arrow/Parquet/IPC serialisation with schema fingerprints. So the port is a
   capability gap, not a missing module.

4. **Capability gap, voiage vs vop_poc_nz** (both declare contract 1.1.0):
   | Capability | voiage | vop_poc_nz | action |
   |---|---|---|---|
   | value of perspective / optimal strategies | yes | yes (`evop`) | already present |
   | Arrow/Parquet/IPC + schema fingerprint | yes | no | keep voiage's |
   | Pareto strategy indices | yes | no | keep voiage's |
   | acceptability frontier | **no** | yes | port |
   | mixture frontier, exact expected-value frontier | **no** | yes | port |
   | expected-value switch points | **no** | yes | port |
   | weighted perspective | **no** | yes | port |
   | MCDA feature records, `tensor_from_records` | **no** | yes | port |
   | `NetBenefitTensor` container + row/segment/switch dataclasses | **no** | yes | port |

5. **Precedent for cross-repo incorporation in this owner's ecosystem**: voiage itself
   carries `.repo-tools/` submodules (sourceright, authentext, astro-polyglot). That is
   noted for the v14-03 CI/pattern decisions, not as a reason to add submodules here.

## Status

- 4.1 (voiage installable on 3.15) — **CORRECTED BY RECONNAISSANCE**: voiage `main` already
  declares `pyarrow>=26.0.0,<27`, `requires-python = ">=3.15.1,<3.16"`,
  `target-version = "py315"` and builds `cp315-abi3`. The `pyarrow<26` cap survives only in
  the **published 2.2.0 tag** and in frozen historical files (`paper/reproduction-environment/…`,
  `packaging/easybuild/release-pyproject-v2.2.0.toml`, and the upstream-owned, SHA-pinned
  `specs/integration/vop-voiage/compatibility/v1/contract.json`). So this task becomes
  "obtain a voiage release containing main's state", not "widen a cap" — and it is
  **release-gated, not code-gated**. Earlier entries in this ledger that framed it as a cap
  change are superseded by this paragraph.
- 4.2 (capability port) — scope confirmed by the dossier: voiage has **no** naming collisions
  for the seven functions or the dataclasses to port (verified by grep across
  `voiage/ tests/ specs/ scripts/`), but the port must be adapted, not copied:
  - voiage raises through `voiage.exceptions.raise_input_error`, not a local
    `PerspectiveError(ValueError)`;
  - voiage is ndarray-first (`ValueArray`), while `vop_poc_nz` is container-first
    (`NetBenefitTensor`);
  - default tie policy differs (`"first"` vs `SPLIT`) and the tolerance keyword differs
    (`tie_tolerance` vs `atol`);
  - `vop_poc_nz` exposes population scaling, the per-person/population split and
    `discordance_probability`, which voiage's perspective module does not expose at all
    (its `Perspective.population` metadata is currently unused);
  - rank-averaging tie semantics from `vop_poc_nz` (`_tie_mask`, `_dense_descending_ranks`,
    `_select_single`) are not reproduced in voiage.
  Two latent collisions must be resolved deliberately: module-level `evop`, and
  `regret_matrix` (voiage already has an ndarray attribute of that name on
  `ValueOfPerspectiveResult`).
- 4.3 (release) — **owner action likely required**: releases are tag-driven
  (`release.yml` on `push: tags: ["v*"]`) and stage a draft with `publish` defaulting to
  `false`; `changelog.md`/`todo.md` entries are required per change. A voiage release
  containing 4.2 is the gate for 4.4 here.
- 4.4 (consume voiage here, with parity) — not started. Weight to record against the
  design document's "value per dependency" criterion: voiage brings **pyarrow** (large
  binary) plus its own stack into this project's resolved set.
- 4.5 (retire duplicates) — not started; `vop_poc_nz` stays an evidence source.

Governance constraints recorded from the dossier that shape 4.2/4.3:
`specs/frontier/governance/promotion-checklist.json` currently registers
`value_of_perspective` as fixture-backed with `next_gate: cross-language-parity` and
`stable_claim_allowed: false`, so new functions must not claim stability; any new Arrow
output field changes `arrow_schema_fingerprint_sha256` and both golden hashes in
`specs/frontier/perspective/v1/interchange/manifest.json`, and reference fingerprints
accept no globs or automatic refresh, so regeneration is a deliberate reviewed step;
`tox run-parallel -p 2` is voiage's local CI authority, and `sys.version_info[:3]` must be
`(3, 15, 1)`.

