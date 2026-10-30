# Current outputs and provenance implementation plan

**Goal:** Current outputs and provenance.
**Architecture:** existing exact pathway model, small standard-library adapters, explicit source and artifact provenance.
**Stack:** Python/NumPy; optional reporting libraries; existing assurance tools.
**Spec:** `v12-02-artifacts-provenance/spec.md`.

## 1. lineage
Create quality/artifacts.py; release file and generating-input manifests; verify actual bytes, source and output inventories; nonrecursive and root-bounded.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 2. regeneration
Regenerate the 44 paired analyses and corrected age-11 utility scenarios into outputs/v12. Export resolved inputs and budgets. Derive current reports/tables from these outputs; mark old reports historical.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 3. receipt
Add generated-artifact dependency fingerprint to assurance and bind pre/post-run snapshots. Configure the current evidence version once. Freeze covered files before the final run; only append excluded evidence afterwards.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

