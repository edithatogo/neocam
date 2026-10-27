# Verify refinements without reissuing unsupported economic claims: implementation plan

Track: `v3-05-final-verification-and-packaging`

## Constraints
No new model parameters. No pandas or xarray. NumPy remains numerical; Polars is the only allowed DataFrame library. No external publication or global environment mutation.

### Task 01: Run full local tests
- [ ] Re-run all collected ordinary tests, then explicit generative/mutation/tool gates; never infer success from config.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 02: Inspect result invariance
- [ ] Check default outputs and source hashes against v2; document every material difference.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 03: Review all changes
- [ ] Separate author review of diff, evidence and incomplete gates; no fabricated independent review.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 04: Complete track statuses
- [ ] Mark implemented code distinct from executed-tool acceptance and unresolved science.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 05: Package reproducible history
- [ ] Create Git bundle, source ZIP, detailed change report, input audit and verification receipt with real paths.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.
