# Neocam / Panda Vision v8 — unified assurance and private-repository handoff

Date: 29 October 2026.

## Verdict

The full unified local harness **finished all 30 mandatory gates**, with **7 passed, 22 blocked, 1 failed**.
The run was unsuccessful overall (exit 1); `run_finished=true` is not `full_local_assurance=true`.
The ordinary covered suite passed **497 tests** in 44.31 seconds. No clinical/economic parameter,
numerical module or retained scientific evidence file changed relative to v7.

The GitHub import is **partial**: bootstrap, connected environment-check workflow, v8 repair patch and
status are on private `edithatogo/neocam`. Complete model source, generated artifacts, source originals
and the local Git history have **not** been uploaded. They are supplied in the complete ZIP/bundle.

## Repairs actually implemented

1. Executable permission/format errors produce a failed receipt instead of aborting the pipeline.
2. Undecodable tool output is retained with replacement characters rather than crashing decoding.
3. An atomic JSON checkpoint is written before and after each gate.
4. Checkpoints include a run ID, active gate and explicit unfinished/unsuccessful state.
5. `--evidence-version v8` separates current evidence and dependent profile files from v7 evidence.
6. Missing native binaries resolve to an explicit missing path, avoiding inaccessible PATH entries.
7. Current CI/runbook point to v8 evidence. Nine new regression tests exercise the repairs.

The initial pre-repair run and failing regression tests are retained in `verification/v8`.
The explicit notebook environment flag avoids unrelated host spreadsheet warm-up. Automatic host
pytest-plugin loading is disabled for the ordinary suite; dedicated required Hypothesis/mutation
gates remain present and blocked where their tools are absent.

## Verification

- Source at execution: `7f8cf5a7594ef5dce1f63579041cca1956166cfe`
- Input/source fingerprint: `3cd4727f50e98c89594beab0156c2cd3ed53f1a0570f5c00acfbd277c6e31a88`
- Run ID: `37b23e38-f2ca-45d6-9426-1b08c8f30439`
- Ordinary tests: **497 passed**
- Scoped combined statement/branch coverage: **94.33%**
- Active numerical-core combined coverage: **96.40%**
- Clinical pathway module: **100%**
- Every gate's log file and SHA-256 match its receipt.
- `git diff eabbb6b -- src data evidence` is empty.

Passed gates: pytest, inputs, context, source_integrity, coverage, coverage_threshold, core_coverage.

The failed `dependency_consistency` gate correctly rejects the missing real `uv.lock`.
Blocked gates are the unavailable requested external tools, their dependent outputs, native/version
and locked-environment verification, Polars reconciliation, and the actual Conductor checkout.
No lint/type/property/mutation/security pass is inferred from configuration. Gitleaks has **not** passed.

## Remote actions performed

- Verified private repository and empty initial contents; did not overwrite an existing project.
- Initialised the repository and uploaded an explicit dependency-resolution workflow.
- Triggered actual run **40721279349**. GitHub reports failure with zero reported steps and runner ID 0.
- No workflow log was retrievable. The cause is not established; do not infer billing, permissions,
  dependency resolution or code failure from this alone.
- Uploaded the repair patch; its Git blob SHA matches the exact local patch bytes.
- Published remote commit **5655915c3e5df30805dafc7eca56cc8772880985**.
- Direct `git push` to the separate conductor branch failed on DNS resolution.

This is not a full model upload, hosted model CI pass, independent clinical validation, procurement
approval or public release. The repository remains private. Restricted originals were not uploaded.

## Reproduce and complete the import on an authorised connected machine

```bash
git clone Panda_Vision_project_v8.bundle neocam-source
cd neocam-source
git remote set-url origin https://github.com/edithatogo/neocam.git
git push -u origin HEAD:refs/heads/conductor/neocam-v8-assurance-publish
```

Do not force-push main. The separate branch preserves the working project history.

The full harness command is:

```bash
OAI_IS_JUPYTER_KERNEL=false PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 \
  python -u -m quality.cli --profile full --evidence-version v8
```

Use the runbook to resolve and review a genuine lock, install the pinned isolated stack, populate
the submodule, and address actual external-tool diagnostics. No missing tool is a pass.

## Remaining scientific requirements

The four core full texts, current QEP/local allocation inputs, originals archive, clinical-effect
validation and truly independent review remain as documented in v7. This engineering pass neither
changes their estimates nor claims that these gaps have been resolved. Existing v7 documents,
tables and plots remain the current analytical outputs.

## Packaging check

The complete source ZIP and Git bundle include all tracked project material and history as
appropriate. A separate restoration test is recorded in `bundle_restore.txt`; its outcome must
be read rather than assumed.
