# Sequential acceptance and recovery implementation plan

**Goal:** reconcile the existing tracks with actual evidence and continue private PR #3.
**Architecture:** keep the exact model and single assurance command; no new modelling framework.
**Tech stack:** existing Python/NumPy model, standard-library verification, Git, GitHub connector.
**Spec:** `conductor/tracks/v10-acceptance-reconciliation/spec.md`.

## Global constraints
No clinical input changes, no fabricated lock, no ignored failing gate, no force push, no public release.

## Review focus
Preserve newer remote work; nonempty source scope; malformed manifests; versioned evidence paths; false claims about partial uploads.

## Tasks (execute in order)
1. [x] Recover v8 and reconcile the v9 code from PR #3 by Git blob hash; execute its ten regression tests.
2. [x] Reproduce source-audit shape/version defects; fix with regression tests and preserve old reports.
3. [x] Inspect each historical plan, run its scoped tests, record remaining acceptance and commit before proceeding.
4. [x] Execute one full covered assurance run; record failed/blocked/passed gates without relaxing requirements.
5. [x] Push tested repairs, quality support, twenty reconciliation records and their logs into existing draft PR #3, preserving two concurrent updates. Full binary/history import remains open; final remote hashes and exact remaining scope are recorded in the handoff.
6. [x] Restore the integrated local source bundle and verify its tests and integrity (516 passed); record the final evidence and package manifest at handoff. Full remote import remains a distinct open requirement.

Pre-flight: the full run consumes the same source-audit CLI checked in task 2. Per-track regression counts overlap and cannot be summed. Local v8 ancestry and remote bootstrap/v9 ancestry remain separate until full import can preserve both.
