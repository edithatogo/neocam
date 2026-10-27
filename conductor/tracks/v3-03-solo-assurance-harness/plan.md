# Use one explicit gate runner for local development and CI: implementation plan

Track: `v3-03-solo-assurance-harness`

## Constraints
No new model parameters. No pandas or xarray. NumPy remains numerical; Polars is the only allowed DataFrame library. No external publication or global environment mutation.

### Task 01: Test failure semantics
- [ ] Reproduce duplicate/conflicting gate receipts, swallowed failures and incomplete release acceptance.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 02: Configure Ruff comprehensively
- [ ] Enable ALL, preview lint/format, import and annotation checks, narrow documented formatter/test exceptions, and forbid unsafe automated fixes.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 03: Configure two type checkers
- [ ] Require ty all-errors and basedpyright strict; record named scope and avoid ignore-all or baseline suppression.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 04: Add generative and mutation checks
- [ ] Expand Hypothesis invariants and configure all five pytest-gremlins operators; mutation threshold errors must block release.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 05: Add profiling and security/prose checks
- [ ] Provide deterministic Scalene workload, gitleaks history+tree scans with redaction, Vale local styles and dependency audit.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 06: Run a fail-closed unified harness
- [ ] Record command, status, exit code, tool version, input fingerprint and log hash for each gate; continue to collect all failures.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 07: Verify receipts
- [ ] Test stale/tampered/duplicate/missing receipts and classify unavailable tools separately from failing checks.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 08: Commit harness evidence
- [ ] Save partial and full gate receipts without equating them to hosted CI.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.
