# Execution ledger — v14-01 engineering rigour

1.0 Design authority recorded in `conductor/v14-design.md`: measured dependency audit
(installed versions), the "foot in two camps" decisions D1–D5 with options, rationale,
tradeoffs and contingencies, and the deliberate non-violations that must not be
"fixed" later.

1.1 reportlab incorporation: owner decision — incorporate, do not remove. Not started;
begins with a reproducing test that fails while reportlab is unused.

1.2–1.4 testing/static-analysis depth and experimental trials: not started. Each trial
records a before/after measurement and is reverted if it does not pay for itself.

1.5 validation-replacement spike (msgspec/pydantic vs bespoke harness validation): not
started; harness-only, measured, and not merged without its own review.

Context from the preceding engineering wave (already landed, see
`verification/v13/burndown/`): Python 3.15-only policy; ruff/ty/basedpyright at maximum
strictness; SHA-pinned hardened CI with CodeQL, dependency-review, Scorecard and
attestation; mutation score raised from 69.78% to 99.52% (gate green); 1,027 tests.
