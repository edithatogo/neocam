# One authoritative, non-duplicating assurance workflow: implementation plan

**Global constraints:** no new clinical inputs; Polars-only DataFrame engine; no hidden environment installation, remote push, relaxed acceptance thresholds or manufactured lockfile.

**Review focus:** stale caches; deleted inputs; false passes from missing tools; duplicated suites; missing artifact-to-analysis links.

## Task 1: Document and reproduce duplicate suite execution

**Status:** accepted. **Evidence:** `profiles_red.txt; full/pytest.txt`.
Files: `tests/test_v4_profiles.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_profiles.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 2: Run ordinary tests once under coverage for PR/full acceptance

**Status:** accepted. **Evidence:** `test_v4_profiles; full/pytest.txt + full/coverage.txt`.
Files: `quality/cli.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_profiles.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 3: Add workflow linters and manifest-verified actionlint installation

**Status:** implemented; external execution blocked. **Evidence:** `checksum metadata and unit tests; actionlint/zizmor unavailable`.
Files: `quality/bootstrap.py; quality/native-tools.json`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m pytest tests/test_v4_profiles.py tests/test_native_integrity.py -q` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.

## Task 4: Integrate prek and one dependency-maintenance bot

**Status:** implemented; integration blocked. **Evidence:** `hook/config tests pass; prek/Renovate activation unverified`.
Files: `.pre-commit-config.yaml; renovate.json; .github/workflows/ci.yml`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m pytest tests/test_v4_config.py -q` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.

## Task 5: Benchmark repeated serial suite versus single covered suite

**Status:** partial measurement. **Evidence:** `benchmarks/measured_work.json; combined repeated driver interrupted`.
Files: `quality/benchmark.py`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m quality.benchmark --repeats 3` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.

## Task 6: Attempt actual external tools and preserve blockers

**Status:** attempt complete; acceptance unsuccessful. **Evidence:** `full/receipt.json: blocked tools and missing-lock failure`.
Files: `verification/v4/full`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m quality.cli --profile full` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.

## v11 reconciliation

Scoped regression command executed successfully; see `reconciliation-v11.json` for the exact code, command and log hash. This does not close unexecuted integration, scientific, archival or hosted acceptance.
