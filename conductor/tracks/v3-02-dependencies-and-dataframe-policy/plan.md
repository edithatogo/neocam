# Refresh direct releases without inflating runtime: implementation plan

Track: `v3-02-dependencies-and-dataframe-policy`

## Constraints
No new model parameters. No pandas or xarray. NumPy remains numerical; Polars is the only allowed DataFrame library. No external publication or global environment mutation.

### Task 01: Verify latest release targets
- [ ] Check primary registries/releases and distinguish current web evidence from installed versions.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 02: Declare minimal dependency groups
- [ ] Keep NumPy numerical core; allow only Polars for DataFrames; segregate reporting and assurance tools.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 03: Reject forbidden dependencies
- [ ] Test AST imports and resolved-lock distributions for pandas/xarray; do not ban mentions in explanatory prose.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 04: Create reproducible lock workflow
- [ ] Implement uv lock generation as an explicit maintenance command; normal CI uses frozen committed lock only.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 05: Resolve and install target stack
- [ ] Run online resolution/install; record blocked status rather than creating a fabricated lock.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 06: Verify compatibility
- [ ] Check requested tools and dependency graph on supported Python; preserve evidence if unavailable.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.

### Task 07: Commit manifest and policy
- [ ] Record exact target/source/date, installed environment and lock limitation.
- [ ] Verify with the track-specific test/command; retain its complete exit status and log.
- [ ] Update this track metadata and commit the completed work, or record the exact blocker.
