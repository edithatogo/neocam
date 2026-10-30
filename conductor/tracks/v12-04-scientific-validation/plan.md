# Scientific and publication validation implementation plan

**Goal:** Scientific and publication validation.
**Architecture:** existing exact pathway model, small standard-library adapters, explicit source and artifact provenance.
**Stack:** Python/NumPy; optional reporting libraries; existing assurance tools.
**Spec:** `v12-04-scientific-validation/spec.md`.

## 1. predictive
Export prior-predictive summaries from the active pathway model with checks for mass conservation, unsupported critical avoidance and signed perspective reconciliation; do not call assumptions posterior fitting.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 2. properties
Move principal Hypothesis properties to active configuration/pathway/perspective routines; retain historical regressions and add end-to-end declared-input/output tests.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

## 3. review
Add clinical plausibility review, external comparison, four full-text gaps, consent/privacy/licensing/publication checklist. Mark empirical review unexecuted. Track repeated contacts and mixed deployment as bounded follow-on analyses, not new asserted effects.
- [ ] Reproduce the relevant failure or missing contract.
- [ ] Implement the smallest correction and run focused regression tests.
- [ ] Record acceptance boundary, update this track and commit before progressing.

