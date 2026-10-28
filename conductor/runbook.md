# Neocam v8: authoritative assurance and private repository handoff

Read conductor/current-state.json and tracks/v8-assurance-publish/{spec,plan}.md.
For CI and dependency work also read .agents/skills/maintaining-lean-ci/SKILL.md.

## Scientific scope
The active model, parameters, source tables and v7 numerical results are unchanged.
Use src/pathways_v6.py with the regional/perspective adapters documented in conductor/runbook-v7-history.md.
data/v6/spec.json is a reference snapshot, not a live configuration input.
Sources and estimates retain the v7 evidence limitations. Do not recast cost-only results as health benefits.

## Authoritative verification
python -m quality.cli --profile full --evidence-version v8
The v7 default path is retained for backward-compatible fixture callers; explicitly select v8 for this handoff.
The same full gate set remains mandatory. Atomic receipts are checkpointed before and after every gate.
run_finished=true means all gates were enumerated, not that they all passed.
complete_within_profile and full_local_assurance require every required gate to pass.
Unexpected interruption leaves a run_finished=false checkpoint; never promote it to acceptance.
Executable permission/format errors are failed checks; unavailable executables are blocked.
Invalid UTF-8 tool output is retained with replacement decoding, not allowed to crash the run.
Version-specific Scalene validation follows the selected evidence version.

## Current host
Disable the notebook-only warm-up flag in subprocesses: OAI_IS_JUPYTER_KERNEL=false.
The available-host run uses PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 and one BLAS/OMP thread.
Dedicated Hypothesis, mutation, profiling and other extension gates remain required.
This host is not the requested isolated pinned environment; do not fabricate uv.lock or imply all tools passed.

## Private GitHub destination
The user explicitly authorised pushing to edithatogo/neocam; the destination was verified private and initially empty.
GitHub connector reads and text writes succeeded. Direct Git transport failed DNS.
The hosted environment-check workflow failed without reporting executed steps; no cause is asserted.
Remote bootstrap/patch/evidence import is partial. The complete bundle remains the authoritative transport of all files/history.
Do not force-push main, change repository visibility, publish restricted originals, or add credentials.
A clean public research release remains a separate task with licensing and privacy checks.

## Handoff
Preserve exact source commit, input fingerprint, log digests, full terminal receipt and remote upload scope.
Restore and test the complete Git bundle. Report blocked, failed and passed gates separately.
Do not rerun clinical analyses when no scientific input or numerical implementation changed.
