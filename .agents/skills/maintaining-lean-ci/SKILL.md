---
name: maintaining-lean-ci
description: Use when a single-developer analytical repository has slow or duplicated checks, dependency churn, stale test caches, network-blocked verification, conflicting agent context, or claims of assurance that exceed actual execution.
---

# Maintaining lean, evidence-bound CI

Keep the application small and make verification trustworthy. A configured check,
installed tool, cached result and freshly passed acceptance gate are different states.

## Start from the actual repository

Read the current branch, dirty state, runbook, active Conductor track and last
machine-readable receipt. Inventory commands and measured durations before adding
tools. Freeze model parameters, source tables and default outputs during engineering
work. Preserve pandas/xarray exclusions when a project specifies Polars only; NumPy
and standard-library CSV do not require a DataFrame rewrite.

## Use this execution contract

| Scope | Execution | Claim permitted |
|---|---|---|
| Edit loop | Changed-file hooks; optional testmon and incremental mutations | Local feedback only |
| Pull request | Complete ordinary suite once under coverage; required static/input checks | Passed within PR scope |
| Full acceptance | Fresh complete required gate set, reviewed lock and version checks | Full local assurance only if every gate passes |
| Hosted release | Exact-commit CI evidence plus explicit publication authority | Hosted acceptance; publication only after authorised execution |

One covered pytest run supplies both test and coverage evidence. Do not run the same
suite again merely to create another label. Keep one harness authoritative; prek
hooks call its existing tool configurations rather than maintain separate policies.

Benchmark serial, two-worker and four-worker execution on the same suite, repeatedly.
Keep serial when gains are unmeasured or startup dominates. Avoid nested parallelism.
Cache download artifacts rather than virtual environments or acceptance receipts.
Cancel obsolete PR runs, not release acceptance. Use one dependency bot and reviewed
updates; ordinary CI checks the lock then uses frozen installs.

## Cache invalidation is part of correctness

Testmon does not observe arbitrary CSV/configuration or external-service changes.
Invalidate local selection when data, configuration, dependency locks, interpreter,
installed dependencies, fixtures or test infrastructure changes. Include deletions
and renames. Mutation caches need the same controls and source/test hashes. Seal a
cache only after actual success; never convert zero collected tests into a pass.
Full acceptance clears incremental evidence. Required unavailable tools remain blocked.

## Keep context and tool selection bounded

AGENTS.md and GEMINI.md point to one short runbook and active track. Each task records
files, a reproducing test, acceptance command, evidence and implemented/accepted/blocked
states. Pin verified releases and action SHAs. Record latest target separately from
installed and tested versions. A newer prerelease is not automatically a better default.

Ruff, ty, basedpyright, Hypothesis, Gremlins, Scalene, Gitleaks, Vale, actionlint and
zizmor have distinct roles. Add no overlapping orchestrator or scanner without a
specific uncovered failure. Missing network access is not permission to fabricate a
lockfile, lower thresholds or repeatedly retry an unchanged blocker.

## Handoff shape

Provide the immutable repo/bundle, command/results receipt, preserved-input comparison,
analysis inventory, plots/tables and requested documents. Report measured speed changes
with counts, repetitions, scope and host. Separate unresolved model evidence from
software defects. State whether hosted CI, tool execution and independent agent review
actually occurred. Never promise permanent cross-chat skill installation from a ZIP.

Run the portable checker with an independently specified gate set and current fingerprint:

```bash
python scripts/audit_evidence.py receipt.json --root . \
  --required tests,inputs,mutation --fingerprint EXPECTED_SHA256
```

This detects inconsistent evidence; it is not a cryptographic attestation. See
`references/acceptance-scenarios.md` for adversarial cases and validation boundaries.
