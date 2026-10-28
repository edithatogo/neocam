# Regenerated decision analysis and publication artifacts

Approved scope: user requested implementation of the preceding recommendations and refreshed artifacts. No new clinical parameters or model features. Preserve the 27-input specification and explicitly uncertain evidence.

## Design
Retain the small Python model and existing harness. Optimize redundant execution before adding optional plugins. Use local-only guarded caches, one covered suite per acceptance run, and separate quick/PR/full scope. Keep original results reproducible. Package a reusable skill; do not claim independent-agent validation or global installation.

## Alternatives
A new CI orchestration framework was rejected as unnecessary. Selective tests are development-only; distributed execution is benchmark-gated. Full fresh acceptance remains mandatory.
