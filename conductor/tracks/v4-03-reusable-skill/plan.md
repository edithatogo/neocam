# Reusable lean assurance skill: implementation plan

**Global constraints:** no new clinical inputs; Polars-only DataFrame engine; no hidden environment installation, remote push, relaxed acceptance thresholds or manufactured lockfile.

**Review focus:** stale caches; deleted inputs; false passes from missing tools; duplicated suites; missing artifact-to-analysis links.

## Task 1: Record observed baseline failures and adversarial scenarios

**Status:** accepted as observed-history baseline. **Evidence:** `skill_baseline.md; no fresh-agent baseline claimed`.
Files: `verification/v4/skill_baseline.md`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_skill.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 2: Create bounded portable SKILL.md and scenario guide

**Status:** accepted within author/contract scope. **Evidence:** `bounded SKILL.md and scenario guide`.
Files: `.agents/skills/maintaining-lean-ci`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_skill.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 3: Provide executable portable evidence-contract verifier

**Status:** accepted. **Evidence:** `skill_scope_red.txt → skill_scope_green.txt`.
Files: `.agents/skills/maintaining-lean-ci/scripts/audit_evidence.py`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m pytest tests/test_v4_skill.py -q` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 4: Link one canonical skill from developer entrypoints

**Status:** accepted. **Evidence:** `AGENTS.md/GEMINI.md link one canonical skill`.
Files: `AGENTS.md; GEMINI.md`
- [x] Write/reproduce the relevant failure or inventory gap.
- [x] Implement the smallest repair without changing economic assumptions.
- [x] Run `python -m quality.checks context` and inspect its actual outcome.
- [x] Record implemented / accepted / blocked separately and commit.

## Task 5: Verify pressure fixtures and distinguish static tests from agent evaluation

**Status:** partial validation. **Evidence:** `16 contract tests; independent fresh-agent pressure evaluation blocked`.
Files: `verification/v4/skill_validation.json`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python -m pytest tests/test_v4_skill.py -q` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.

## Task 6: Package portable skill without claiming global ChatGPT installation

**Status:** packaged; restoration verified at handoff. **Evidence:** `versioned standalone skill ZIP; no global install`.
Files: `outputs/v4`
- [ ] Write/reproduce the relevant failure or inventory gap.
- [ ] Implement the smallest repair without changing economic assumptions.
- [ ] Run `python scripts/package_v4.py` and inspect its actual outcome.
- [ ] Record implemented / accepted / blocked separately and commit.
