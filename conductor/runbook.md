# Single-developer runbook

## Scope and authority

This branch refines the existing model, inputs and assurance. It adds no clinical parameters or model features. The v2 economic artifacts remain historical outputs; default-result parity is checked in `verification/v3/default_output_parity.json`.

Use this precedence: explicit user request; current design/specification; parameter/source registers; implementation plan; code; generated reports. An estimated input is not an observed value. Tests certify implementation behaviour, not clinical effectiveness or local cost validity.

## Minimal development loop

1. Read `conductor/current-state.json`, `conductor/tracks.md`, and only the next track's spec/plan. Do not load old reports or whole external repositories by default.
2. Check Git status and preserve unrelated work. Add a failing regression test before changing behaviour.
3. Implement the smallest repair, then run `python -m quality.cli --profile quick`.
4. For a pre-push/release review, run the full profile below. Read every failed and blocked gate. Missing executables never count as successful checks.
5. Update the track with exact commands, actual receipts, unresolved issues and the next step. Commit changes with a clear scope. No remote push or publication is implied.

## Reproducible environment

`pyproject.toml` is the only active source for Python dependency pins. `quality/native-tools.json` pins Gitleaks/Vale release binaries and their hashes. NumPy handles numerical vectors; the optional Polars extra provides independent table reconciliation. Do not install Hypothesis `all`/`pandas` extras.

On a connected development machine, create and review the missing lock once:

```bash
python -m pip install uv==0.13.6
uv lock --upgrade
python -m quality.checks lock
uv sync --frozen --group assurance --extra tabular
uv run --frozen --group assurance --extra tabular python -m quality.bootstrap
git submodule update --init --recursive
uv run --frozen --group assurance --extra tabular python -m quality.cli --profile full
```

Normal CI never re-resolves dependencies. Commit the reviewed real `uv.lock`; do not fabricate a lock from direct pins. Any latest-version conflict is a blocker to resolve, not permission to silently downgrade or bypass the requested tool.

## Gates and acceptance

The **quick** profile checks all ordinary tests, input-register reconciliation and context integrity. It is a feedback loop, not release certification.

The **full** profile adds branch coverage, Ruff ALL/preview plus formatter checks, ty all-errors, basedpyright all-rules, Hypothesis, all five Gremlins operators, explicit mutation-score validation, Scalene CPU/memory profiling, Gitleaks history and tree scans, Vale prose checks, exact dependency versions, a hashed lock, vulnerability audit/SBOM, the Conductor checkout, and a Polars reconciliation.

Coverage targets are acceptance criteria, not achieved claims: 90% overall for model/harness and 95% for the active numerical module. Mutation acceptance requires at least 90% zapped, nonzero mutations, and no errors, timeouts or pardons. These are choices for this project. Any later exception requires a documented decision and a test, not an ignore-all baseline.

Ruff global exceptions are only COM812/ISC001 formatter conflicts. Test assertions and literal expectations are allowed only in test files. Unsafe automatic fixes are disabled. Experimental typing semantics are disabled because they are unrelated to the model; strict checking remains enabled.

Scalene runs a fixed existing PSA workload, without AI suggestions, uploading code or hardware-specific performance promises. Do not infer a performance regression from unlike hosts.

## Evidence and context hygiene

The harness stores command, exit code, duration, input fingerprint, log digest and installed versions. It rejects duplicate, missing, failed, stale or altered receipts. Logs are evidence, not cryptographic attestation. Source and input hashes do not validate unknown clinical assumptions.

Keep AGENTS/GEMINI under 6 KB each. The task ledger, decision record and evidence register are authoritative; conversation memory is not. Do not mark blocked external-tool acceptance complete merely because configuration exists.

## Current execution boundary

The supplied environment runs Python 3.13.5 with older numerical/test packages. DNS/package downloads are unavailable. Full dependency installation, Ruff/type/generative/mutation/profiling/security/prose execution and hosted CI remain unverified until their actual receipts pass. The full runner returns nonzero while these are blocked.

The 2022 source births, assumed cost/effect inputs and unresolved QEP remain visible. No assumptions are upgraded to evidence during this engineering pass.
