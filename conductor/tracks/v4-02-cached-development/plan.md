# Safe incremental feedback without incremental acceptance: implementation plan

**Global constraints:** no new clinical inputs; Polars-only DataFrame engine; no hidden environment installation, remote push, relaxed acceptance thresholds or manufactured lockfile.

**Review focus:** stale caches; deleted inputs; false passes from missing tools; duplicated suites; missing artifact-to-analysis links.

## Task 1: Specify data/config/environment cache invalidation tests

**Status:** accepted. **Evidence:** `cache_red.txt; refinement_green.txt`.
Files: `tests/test_v4_feedback.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_feedback.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 2: Build guarded local testmon and incremental-mutation entrypoint

**Status:** implemented; plugin integration blocked. **Evidence:** `test_v4_feedback.py passes; testmon unavailable`.
Files: `quality/feedback.py`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m pytest tests/test_v4_feedback.py -q` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.

## Task 3: Require pass-only cache seals; bind dependency and interpreter versions

**Status:** accepted within contract scope. **Evidence:** `tests cover failed, stale, deleted-input and changed-environment seals`.
Files: `quality/feedback.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_feedback.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 4: Keep fresh release evidence; do not treat no-tests-collected as a pass

**Status:** accepted within contract scope. **Evidence:** `clean full command retained; no-tests status not promoted`.
Files: `quality/cli.py; quality/feedback.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_feedback.py tests/test_v4_profiles.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 5: Benchmark optional xdist workers; retain serial default absent evidence

**Status:** blocked; serial retained. **Evidence:** `xdist/testmon not installed; no speed claims`.
Files: `quality/benchmark.py`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m quality.benchmark --repeats 3` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.

## Task 6: Record local-only cache and environment limitations

**Status:** accepted. **Evidence:** `runbook + current-state document actual bounds`.
Files: `conductor/runbook.md`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m quality.checks context` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.
