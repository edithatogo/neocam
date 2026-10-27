# V3 author self-review

This is a scoped author review, not an independent expert/code review.

## Confirmed repairs

The original PSA ignored a supplied odds ratio in the attenuated structure. Site loading lost the input year and accepted duplicate facility rows. Numeric contracts accepted booleans as costs and mutable sequences inside frozen parameters. Very small positive discount rates caused cancellation in annuity calculations. Reproducing tests were run before repairs and default result parity was rechecked.

The prior verifier could mislabel an import/program failure as a dependency blocker and had a partial-CI bypass. The new runner binds every required gate to source/input fingerprints and log hashes, rejects duplicate/stale/tampered evidence and runs all declared checks without a successful-release fallback. A designated exit-69 preflight is distinguished from an ordinary failing command.

Review of native installation found that a checksum mismatch was grouped with network unavailability. Integrity failures now fail. URLs are restricted to HTTPS GitHub release assets, only an exact regular executable is extracted, and native versions are independently checked. Fixtures test these boundaries; they are not evidence of actual native scanner execution.

Review of CI portability found a test depending on this host not being the project environment. The test now simulates the host identity; an additional test verifies prohibited installed packages inside a simulated isolated environment. The resolver is pinned and checked alongside other direct dependencies. Scalene no longer uses CPU-only mode while documentation promises CPU and memory profiling.

## Remaining limits and first connected run

No real lock, target environment or Conductor checkout was obtained. The latest versions were identified from primary release sources but cannot be described as installed/tested. Ruff ALL/preview, ty and basedpyright are strict configurations awaiting first execution; formatting/type diagnostics may still exist. Do not claim those gates clean. Hypothesis, Gremlins, Scalene, Gitleaks, Vale, pip-audit/SBOM, Polars and hosted CI likewise require actual successful runs.

No mutation score or profiling result is supplied. Mocked metadata, installer and receipt fixtures test harness behaviour only. Coverage excludes the explicitly separately gated generative/Polars/profiler workloads; the report does not pretend these ran under ordinary pytest.

Input audit establishes schema/grain, field/register consistency, references, source hashes and arithmetic, not empirical local effect/cost validity. No current QEP, new neonatal casemix, new patient data or new clinical parameter is invented. Historical v2 authoring dependencies and artifacts were not rebuilt.

The full outcome remains NOT RELEASE-READY while any mandatory gate is blocked or failed. No remote repository was created or modified, and no independent review was performed.
