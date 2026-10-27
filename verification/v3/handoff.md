# Panda Vision v3 — engineering assurance handoff

**Date:** 28 October 2026. **Status:** model/refinement checks pass in the available host; full requested toolchain acceptance is incomplete. No new clinical or economic parameter or feature.

## Delivered and verified

The ordinary suite passes **254 tests**, increased from the 75-test v2 baseline. Scoped combined statement/branch coverage is **98.52%**; both numerical modules show **100%**. The input and receipt-validation modules also show 100%. These figures do not mean every defect is excluded. Dedicated generative, mutation, Polars and profiler workloads were not executed and are explicitly outside ordinary-suite coverage.

The unified full harness attempted **26 mandatory gates**: **6 passed, 19 blocked, 1 failed**. Its return outcome is unsuccessful and `full_local_assurance=false`. The failed consistency check correctly rejected a missing real `uv.lock`. Fresh lock resolution separately failed on PyPI DNS. Missing tools were not treated as passes.

Verification source commit: `7ad31e211d8fef2ebbfedfe30bc1b867dc47e1ee`. Source/input fingerprint: `44727a3a90d72fdefec6895598502a98a520c9a565c3f4ab7b83fc179807bf3a`. Later receipt-only commits do not alter this fingerprint. No hosted workflow, deployment, remote push or independent code review is claimed.

## Repaired defects

1. Attenuated PSA now honours the supplied odds-ratio parameter instead of ignoring it.
2. Source year is retained and duplicate/blank/mixed-year/negative/non-public or incomplete birth rows are rejected before calculation.
3. Parameter contracts reject booleans as numeric costs and freeze user-supplied sequences as tuples.
4. Scalar and vector annuity calculations remain stable at near-zero positive discount rates.
5. The harness distinguishes program failures, unavailable prerequisites and timeouts; stale, duplicate, incomplete, conflicting or altered receipts cannot certify a pass.
6. Native installer checksum/URL/size failures are failures, not network blockers; release hashes and versions are explicit.
7. CI portability no longer depends on the current host path. The resolver is version-pinned, and profiling configuration matches the documented CPU/memory scope.

Each behavioural fix retains reproducing failure and subsequent passing evidence in `verification/v3/`. These tests include synthetic fixtures; fixtures do not count as real external-tool execution.

## Preserved inputs and economic results

All **27 model parameters** and **nine protected data/evidence files** are unchanged. The source audit reconciles **72 published public-facility rows, 65 aliased sites, 46,711 births, 15 source records and 7 mapped studies**. It checks field values, grain, references, disclosures and arithmetic—not empirical truth of uncertain effects or costs.

Five default deterministic portfolios and the pilot/spoke 20,000-draw PSA arrays were independently compared with the original Git revision, using relative tolerance 1e-12 and absolute tolerance 1e-8. Default economic results match. QEP, local retrieval costs, geographic casemix and clinical effects retain v2's stated uncertainty. No further empirical data collection or structured elicitation was imposed.

## Dependency verification versus execution

The target releases were located using primary registries/release metadata. They are pinned, but **not installed or compatibility-certified here**. The Python host is 3.13.5. Python 3.13/3.14/3.15 CI is configured, not executed.

| Component | Verified target | Available host |
|---|---:|---:|
| numpy | 2.5.4 | 2.3.5 |
| polars | 2.1.0 | Unavailable |
| pytest | 9.1.1 | 9.0.2 |
| coverage | 7.17.0 | 7.13.3 |
| ruff | 0.17.3 | Unavailable |
| ty | 0.0.92 | Unavailable |
| basedpyright | 1.40.2 | Unavailable |
| hypothesis | 6.170.12 | Unavailable |
| pytest-gremlins | 1.12.2 | Unavailable |
| scalene | 2.4.0 | Unavailable |
| pip-audit | 2.10.1 | Unavailable |
| uv | 0.13.6 | 0.10.0 |
| gitleaks | 8.30.1 | Unavailable |
| vale | 3.25.1 | Unavailable |

Primary locators and dates are recorded in `evidence/dependency_targets_v3.json`, `quality/native-tools.json`, and `evidence/conductor_pin_v3.json`. A direct-pin list is not a transitive hash lock. None has been fabricated.

Polars is the sole permitted DataFrame engine; no pandas/xarray imports or declared project dependency are introduced. AST and lock/installed-environment checks enforce the ban. Since the genuine dependency graph cannot yet be resolved, its complete transitive absence is not certified. NumPy remains the numerical engine and standard-library CSV handles the small tables. Polars is an independent tabular-check extra rather than an unnecessary whole-model rewrite. The pandas-backed mchs runtime is not imported.

## Requested tools

Ruff selects ALL rules and preview diagnostics, checks formatter output and formats docstring code, and disables unsafe automatic fixes. The only global rule exemptions are documented formatter conflicts; test assertions/literal expectations are scoped to tests. ty uses all-error diagnostics and basedpyright all-rule checking, with no broad ignore/baseline file.

Eight Hypothesis properties, all five Gremlins operator classes, a >=90% independently checked mutation score, two mutation workers and zero automatic pardons are configured. Zero-mutant, inconsistent, timeout or error reports fail. No mutation score is asserted.

Scalene targets an existing reproducible PSA workload, using CPU/memory profiling without AI suggestions or uploads. Gitleaks checks Git history and the working tree with redaction. Vale uses local controlled prose rules. The audit and SBOM gates inspect an installed environment, not guessed dependencies. All require actual execution before acceptance. A first connected Ruff/type-check run may expose further code/style/type repairs; strict configuration alone does not mean that work is complete.

## Single-developer operation

`AGENTS.md` and `GEMINI.md` point to one runbook. Load current state and the active track rather than the entire historical conversation. The quick loop is ordinary tests plus input/context checks. The full profile is the same explicit entrypoint in local development and hosted CI. Source/input hashes, command, exit status, elapsed time, log digest and installed versions are recorded.

Five granular Conductor tracks contain 34 tasks, exact files/commands, evidence paths and separate implementation/acceptance states. Context and dependency policy are versioned; protected clinical inputs are not silently changed. The Conductor main ref was rechecked and still equals the pinned `137c1e41ff9c1dc75ff277b9582460a0bd8c4768`. Its checkout attempt failed on GitHub DNS; no Conductor CLI execution is claimed.

CI uses SHA-pinned actions, read-only permissions, no automatic publication, a reviewed frozen dependency lock, a Python matrix and bounded receipt artifacts. The ordinary workflow never upgrades dependencies. Dependency maintenance produces reviewable updates rather than auto-merging them.

## Actual full gate results

| Gate | Status | Exit | Evidence |
|---|---|---:|---|
| pytest | passed | 0 | `verification/v3/full/pytest.txt` |
| inputs | passed | 0 | `verification/v3/full/inputs.txt` |
| context | passed | 0 | `verification/v3/full/context.txt` |
| coverage | passed | 0 | `verification/v3/full/coverage.txt` |
| coverage_threshold | passed | 0 | `verification/v3/full/coverage_threshold.txt` |
| core_coverage | passed | 0 | `verification/v3/full/core_coverage.txt` |
| ruff_lint | blocked | Not executed | `verification/v3/full/ruff_lint.txt` |
| ruff_format | blocked | Not executed | `verification/v3/full/ruff_format.txt` |
| ty | blocked | Not executed | `verification/v3/full/ty.txt` |
| basedpyright | blocked | Not executed | `verification/v3/full/basedpyright.txt` |
| hypothesis | blocked | Not executed | `verification/v3/full/hypothesis.txt` |
| gremlins | blocked | Not executed | `verification/v3/full/gremlins.txt` |
| mutation_score | blocked | 69 | `verification/v3/full/mutation_score.txt` |
| scalene | blocked | Not executed | `verification/v3/full/scalene.txt` |
| scalene_output | blocked | 69 | `verification/v3/full/scalene_output.txt` |
| gitleaks_history | blocked | Not executed | `verification/v3/full/gitleaks_history.txt` |
| gitleaks_tree | blocked | Not executed | `verification/v3/full/gitleaks_tree.txt` |
| vale | blocked | Not executed | `verification/v3/full/vale.txt` |
| dependency_consistency | failed | 2 | `verification/v3/full/dependency_consistency.txt` |
| dependency_lock | blocked | 69 | `verification/v3/full/dependency_lock.txt` |
| native_versions | blocked | 69 | `verification/v3/full/native_versions.txt` |
| locked_versions | blocked | 69 | `verification/v3/full/locked_versions.txt` |
| pip_audit | blocked | Not executed | `verification/v3/full/pip_audit.txt` |
| sbom | blocked | Not executed | `verification/v3/full/sbom.txt` |
| conductor_checkout | blocked | 69 | `verification/v3/full/conductor_checkout.txt` |
| polars_consistency | blocked | Not executed | `verification/v3/full/polars_consistency.txt` |

## Remaining acceptance work

On a network-enabled authorised checkout, resolve/review the real lock, install the pinned isolated stack and native binaries, populate the submodule, then execute the full harness and address its actual diagnostics. Do not lower thresholds, generate an ignore-all type baseline, or report unavailable checks as passed. Exact commands are in `conductor/runbook.md`.

This handoff is a tested engineering refinement, **not a claim of complete CI, current installed dependencies, clinical validation or production readiness**. Existing v2 Word/PDF/Excel/PowerPoint outputs are preserved and were not rebuilt during this pass.
