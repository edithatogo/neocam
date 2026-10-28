# Neocam / Panda Vision

Private working destination for the Queensland neonatal teleconsultation economic evaluation.

## Complete model import: still blocked

**This GitHub main branch does not yet contain the full model.** It contains recovery/import tooling, the v8 assurance repair patch, and verification records. The complete source and history have been restored locally and backed up privately in the owner's Google Drive; they have not been transferred into this repository's Git object graph.

### Working private recovery downloads

- **Recommended:** [Ready-to-push ZIP: complete Git repository, compact initial working folder](https://drive.google.com/file/d/1G3viHjF-QGYGKU3_YrZkkitz50d7l0BX/view) — 77,184,933 bytes. Includes the full source tree and all 31 source-history commits in Git. This is a standard ZIP, not a bundle requiring conversion.
- [Full source-file ZIP](https://drive.google.com/file/d/15E2QVVoFtvRIrvdtrFdk7pb81Up0TbF-/view) — 99,087,687 bytes.
- [Original full Git bundle](https://drive.google.com/file/d/12u7z5Hb9_7puJjFYqXgoyjeACbGYHHH9/view) — 76,718,081 bytes.

The Drive files remain private; repository visibility was not changed. Source ZIP bytes match every tracked blob in the restored bundle. The compact ZIP was extracted, expanded to a full checkout, checked with `git fsck`, and pushed to a separate LOCAL bare remote. Those checks passed; they are not a GitHub-upload claim.

After extracting the recommended ZIP, use an authenticated, network-connected Git terminal inside its `neocam` folder:

```bash
git sparse-checkout disable
git push -u origin recovery/complete-v8
```

The first command materialises all tracked outputs and sources. The second transfers all files and source history to a recovery branch without force-pushing or overwriting `main`. No `git init` or bundle conversion is needed. The archive already has the correct private GitHub remote configured. Keep credentials in your normal credential manager, never in the repository or chat.

### Exact transfer acceptance

- Source commit: `7242e7f7e12d807c52e1d250a388541ada033c51`
- Source tree: `0ef76ee21360db34af07a281712ce2f75dc97bd8`
- Source entries: **893**, including the Conductor submodule gitlink.
- Complete source history: **31 commits**.
- [Machine-readable recovery checks and hashes](handoff/recovery/verification.json)
- [Locally tested complete-history importer](scripts/import_repository.py)
- [Open transfer blocker](https://github.com/edithatogo/neocam/issues/2)

The automated importer verifies archive size/SHA-256, source commit/tree and every tracked entry; it preserves both the source and bootstrap histories and uses no force push. Hosted attempts on [Ubuntu 24.04](https://github.com/edithatogo/neocam/actions/runs/40729381504) and [Ubuntu Slim](https://github.com/edithatogo/neocam/actions/runs/40730856006) both failed before runner allocation (`runner_id=0`, `steps=[]`). The underlying account/platform cause is not established. A working runner or authenticated connected Git terminal is still needed. Temporary download credentials were removed from the current import issue body.

## Actual model assurance

The v8 full local harness finished all 30 required gates: **7 passed, 22 blocked, 1 failed**. The restored ordinary suite again passed **497 tests**. This is not full pinned-toolchain certification. The genuine `uv.lock`, unavailable external lint/type/property/mutation/profiling/security tools, and populated Conductor checkout remain unresolved. **Gitleaks has not passed.**

- [Assurance repair patch](handoff/v8/assurance-repairs.patch)
- [Prior assurance status](handoff/v8/status.json)

## Privacy and scientific boundary

The project includes restricted corporate sources and templates and must remain private. No patient-level data were added. Recovery work has not changed clinical/economic parameters. This is a preliminary model, not clinical validation, procurement approval or a production system. Complete scientific evidence review, independent validation and clean toolchain acceptance remain separate from successful transfer.
