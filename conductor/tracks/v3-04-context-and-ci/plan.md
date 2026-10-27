# Make single-developer continuation reproducible: implementation plan

Track: `v3-04-context-and-ci`

## Constraints
No new model parameters. No pandas or xarray. NumPy remains numerical; Polars is the only allowed DataFrame library. No external publication or global environment mutation.

### Task 01: Unify context entrypoints
- [ ] Keep AGENTS.md and GEMINI.md short; route to one current-state file and active track index.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 02: Maintain decision and uncertainty records
- [ ] Write no-feature scope, unresolved-input ledger, context manifest, parameter freeze and source trust rules.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 03: Align CI with local gates
- [ ] SHA-pin actions, least privilege, frozen lock and full source scan; avoid silently weaker --ci path.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 04: Guard releases
- [ ] Require exact-commit gate receipts and explicit private-release approval; do not deploy or publish.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 05: Validate context and workflow structure
- [ ] Run deterministic checks for referenced files, statuses, commands, immutable pins and clean branch.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 06: Attempt submodule materialisation
- [ ] Verify gitlink and attempt checkout; missing network remains an explicit blocker.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 07: Record handoff
- [ ] Commit exact next commands and executable acceptance criteria; do not mark blocked work complete.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.
