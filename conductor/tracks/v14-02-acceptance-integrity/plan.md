# Acceptance integrity implementation plan

Goal: make the acceptance chain self-consistent and reproducible, so a green run means
the sealed artefacts correspond to the exact sources that produced them.
Spec: spec.md and ../../v14-design.md.
Workflow: conductor-implement then conductor-review; keep records. One revertable commit
per task.

## Phase/task 2.1: Source-register and artifact-manifest governance
Files: `sources/manifest.json`; `conductor/runbook.md`; `verification/`.
Interface: the source register pins `sources/retrieve_originals.py` by size and digest, and the artifact manifests pin every calculation input (`analysis_inputs`) plus the generation commit. Any later edit to a pinned file invalidates a previous seal.
Acceptance: the register matches the file on disk, and the ordering rule ("verify, then re-seal last, then verify again; never seal mid-wave") is written where an operator will see it. The current mismatch (cleaned retrieval tool vs its register record) is reconciled with the evidence that the cleaning was behaviour-preserving.

- [x] 2.1.a Reproduce the mismatch: `python -m quality.source_archive` reported size and digest mismatch for `sources/retrieve_originals.py`.
- [x] 2.1.b Preserve the red evidence: the failure text and the AST-identity/byte-identical-stdout proof from the burn-down audit.
- [x] 2.1.c Update the register record to the cleaned file's size and digest; no other field changed.
- [x] 2.1.d `quality.source_archive` now verifies clean; `quality.artifacts verify` still reports the expected stale seal.
- [ ] 2.1.e Record the rule in the runbook, commit and record SHA in progress.md.

## Phase/task 2.2: Full-profile green and hosted evidence
Files: `verification/v13/full/` and `verification/` receipts; no source changes.
Interface: `python -m quality.cli --profile full --evidence-version v13` must pass every gate; the artifact re-seal is the last mutation before the run; hosted CI must reproduce the run on the same commit.
Acceptance: all gates pass in one run, with the reseal immediately before it; the hosted ledger records the same verdicts; any gate that cannot pass is recorded as blocked with its evidence rather than waived.

- [ ] 2.2.a Confirm no source edit remains outstanding before freezing.
- [ ] 2.2.b Re-seal both artifact scopes, then run the full profile immediately afterwards.
- [ ] 2.2.c Record the gate ledger (passed/failed/blocked) in `verification/`.
- [ ] 2.2.d Push the frozen commit and dispatch hosted CI; read back the run and retain its artefacts.
- [ ] 2.2.e Review, commit the receipts and record SHAs in progress.md.
