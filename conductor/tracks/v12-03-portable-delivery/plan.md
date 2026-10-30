# Portable build and verified delivery implementation plan

**Goal:** Portable build and verified delivery.
**Architecture:** existing exact pathway model, small standard-library adapters, explicit source and artifact provenance.
**Stack:** Python/NumPy; optional reporting libraries; existing assurance tools.
**Spec:** `v12-03-portable-delivery/spec.md`.

## 1. commands
Provide one standard-library CLI for current analysis, report building, verification and migration inventory; remove host-specific dependencies from the current build path.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 2. environment
Separate model, reporting and assurance dependencies; keep latest-candidate and actually tested environment distinct. Attempt genuine lock resolution once; no fabricated lock or relaxed gates.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 3. migration
Update existing private PR with tested text files using expected-head writes; report exact transfer inventory and complete-migration blocker. Preserve original ancestry locally; no force push or main merge.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

