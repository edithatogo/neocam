# Preserve model scope and harden verified inputs: implementation plan

Track: `v3-01-input-and-numerical-integrity`

## Constraints
No new model parameters. No pandas or xarray. NumPy remains numerical; Polars is the only allowed DataFrame library. No external publication or global environment mutation.

### Task 01: Reproduce v2 baseline
- [ ] Run the complete 75-test baseline and save the command/output.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 02: Freeze assumptions
- [ ] Hash data and literature inputs; retain 28 existing model fields and original effect structures.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 03: Reproduce integrity failures
- [ ] Write tests for malformed/duplicate/mixed-year rows, mutable frozen inputs, numeric edge cases, and PSA odds-ratio propagation; watch them fail.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 04: Repair data and numeric contracts
- [ ] Validate original CSV grain and dataclasses; preserve years, stabilise near-zero annuities, honour the attenuated effect parameter without changing its default.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 05: Verify economic regression
- [ ] Independently compare v2/v3 default deterministic and same-seed PSA output within explicit tolerance.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 06: Audit provenance
- [ ] Check every input field and source identifier; distinguish sourced, assumed, derived and unverified evidence.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 07: Commit verified repairs
- [ ] Record red/green logs, changed input hashes and remaining evidential limitations.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.
