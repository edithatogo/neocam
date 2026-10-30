# Review Report: v13 episode/contact, deployment, review and delivery tracks

## Summary
Implemented analytical and evidence-contract scope is technically reviewable with disclosed assumptions; external assurance, independent clinical validation and remote publication are not complete.

## Verification Checks
- [x] Plan Compliance: partial overall — three analytical/contract tracks implemented; local integration done; external delivery/acceptance remains blocked.
- [x] Product Guidelines Compliance: pass within author review — no new clinical effect estimates, approval claims, patient records or dependencies.
- [ ] Code Style Compliance: incomplete — author inspection and diff whitespace checks only; mandatory Ruff/ty/basedpyright execution blocked.
- [x] Platform Guide Compliance: NA — no local platform/style-guide directory exists; workflow and product guidelines read.
- [x] New Tests: yes — TDD failure evidence and green runs retained by phase.
- [x] Test Coverage: scoped available-host coverage measured; dedicated Hypothesis and mutation execution remains unavailable.
- [x] Ordinary Test Results:676 passed on final committed source ff0182d; full unified acceptance remains unsuccessful (8passed,22blocked,1failed). Exact receipt/fingerprints are in handoff/v13/status.json.

## Findings and resolutions
### High — review identity did not include calculation source
- File: scripts/analyse_refinements.py, snapshot_identity.
- Context: unchanged configuration could leave a reviewer request referring to changed implementation.
- Resolution: source and resolved inputs jointly determine review snapshot; source-change test reproduced the gap and passes after repair.

### High — artifact CLI checked a hard-coded historical output
- File: quality/artifacts.py, main.
- Context: the assurance configuration declared current outputs but the gate defaulted to v12.
- Resolution: read declared primary and additional output paths, reject invalid scope, verify every declared set. Tampering the supplemental output fails the real CLI contract.

### Medium — duplicate pilot policy labels diluted strategy representation
- File: src/deployment.py, policy_catalogue.
- Context: with only three already-installed pilot sites, four expansion labels describe the same actual assignment.
- Resolution: deduplicate exact assignments before rankings. Pilot has two policies, not six aliases.

### Medium — falsey untyped activity silently became defaults
- File: src/pathways_v6.py, compare_v6.
- Context: False, zero and empty containers were treated like None.
- Resolution: only None constructs defaults; four reproducing failures now reject malformed inputs. Overflow and nonfinite exposure checks retained.

### Medium — avoidable duplicate calculations interrupted full-size runs
- File: src/deployment.py, evaluate_policies; scripts/analyse_refinements.py.
- Context: each alternative recomputed all strategies for shared site groups. Two outer timeouts occurred before completed output tables.
- Resolution: compute each exact group once inside an evaluation call; never persist this state. Inputs remain paired, caller arrays are not modified, returned arrays do not alias. All38arrays for six policies and128draws match the pre-optimisation implementation bit-for-bit. The complete480scenario run at20,000draws now finishes. Interrupted candidates remain clearly labelled, never used as final evidence.

### Important open boundary — clinical eligibility and external review
- Conditional expansion is not an approval. Reported operation is not regulatory certification.
- Source/identity records are requests/attestations, not authentication or independent clinical validation. Four reviewer records remain pending.
- Positive/negative transfer differences remain signed; additional transfer can be appropriate. No utility or mortality gain is inferred.
- Mixed-policy provider/fiscal allocations remain an explicitly open methods question; original six-perspective reference is retained.

## Implementation recommendation
Keep local analytical changes with their explicit assumptions. Do not claim full toolchain acceptance, independent validation, complete migration or a procurement recommendation. Preserve all tracks; no archival deletion.

## Review provenance
Same assistant reviewed the implementation using the pinned conductor-review command protocol after conductor-implement execution. No independent subagent or external reviewer was invoked. Upstream source hashes are in conductor/skill-provenance-v13.json. The Conductor CLI and actual submodule checkout were not executed successfully.

### Medium — stale context and non-executable task placeholder
- Files: conductor/current-state.json; conductor/tracks/v13-04-release/plan.md.
- Resolution: current artifact and remote fields now refer to the actual v13 outputs and last observed PR head; the final delivery phase uses real shell commands rather than a placeholder pytest command. The complete final snapshot is rerun after this repair; no analytical inputs changed.

## Final exact-snapshot verification
Source `ff0182de3933348565ef06e7799aa3c34c827760`:676 ordinary tests passed;31 gates reached,8 passed,22 blocked,1 failed. Coverage93.43%, active core96.53%; activity/configuration/equipment/pathway modules100%. Both final fingerprints and all gate log digests match. Current primary and refinement artifact manifests pass. All12 shared primary CSV files match v12 byte-for-byte. Four external reviewer requests remain pending and their validation command correctly returns nonzero. Final evidence-only appendices are excluded from calculation/verification input scopes; no complete-release, independent-validation or remote-push claim.
