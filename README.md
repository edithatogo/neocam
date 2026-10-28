# Neocam / Panda Vision

Private working destination for the Queensland neonatal teleconsultation economic evaluation.

## Import is PARTIAL

This repository currently contains the import bootstrap, a connected dependency-resolution workflow, the **v8 assurance repair patch**, and the verification-status summary. **The complete model source, data, artifacts and Git history have not been uploaded.** Direct Git transport from the execution environment failed because github.com could not be resolved. The full source ZIP and Git bundle are supplied in the conversation handoff.

- [Assurance repair patch](handoff/v8/assurance-repairs.patch)
- [Machine-readable status](handoff/v8/status.json)
- [Environment-check run](https://github.com/edithatogo/neocam/actions/runs/40721279349)

## Actual verification

The full local harness finished all 30 required gates: **7 passed, 22 blocked, 1 failed**. The ordinary suite passed **497 tests**. This is a completed unsuccessful assurance run, not a clean toolchain or release certification. The failed gate is the absent genuine uv.lock. Required external lint/type/property/mutation/profiling/security tools and the actual Conductor checkout remain unavailable. Gitleaks has not passed.

The connected environment workflow failed before any reported steps; its cause has not been established. No hosted model test pass is claimed.

## Repairs

Executable launch errors now produce a failed receipt rather than aborting the whole run. Invalid output bytes are retained. Evidence is atomically checkpointed before and after every gate, with run identifiers and explicit incomplete state. Missing native binaries are distinguished from permission failures. Nine regression tests cover these changes. Clinical/economic inputs and numerical model code are unchanged.

## Complete the import from the supplied bundle

```bash
git clone Panda_Vision_project_v8.bundle neocam-source
cd neocam-source
git remote set-url origin https://github.com/edithatogo/neocam.git
git push -u origin HEAD:refs/heads/conductor/neocam-v8-assurance-publish
```

This uses a separate branch, does not overwrite main, and preserves the supplied project history. The complete unified command in that source tree is:

```bash
OAI_IS_JUPYTER_KERNEL=false PYTEST_DISABLE_PLUGIN_AUTOLOAD=1 python -u -m quality.cli --profile full --evidence-version v8
```

The notebook flag avoids unrelated host warm-up; explicit property/mutation gates are still mandatory. Install and verify the locked toolchain in an authorised connected environment before expecting full acceptance.

## Privacy and scientific boundary

No patient-level data were added. Restricted corporate originals remain in the private local handoff rather than this partial upload. Keep the repository private. This is a preliminary economic model, not clinical validation, a procurement recommendation or a production system.
