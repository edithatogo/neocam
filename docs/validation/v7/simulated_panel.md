# Simulated review panel — 28 October 2026

**Nature of review:** four sequential role-based reviews by the same assistant that implemented the changes. They are simulated reviewer perspectives, not independent subagent runs, human peer review or external model validation. No fabricated reviewer names, run IDs, approvals or credentials.

## 1. Clinical and regional-service reviewer
Scope: consultation denominator, mandatory transfers, delayed rescue, geography, case-mix, health effects and equity.

Findings: the three-site forecast is calls, not all births and not observed incidence. Regional sites differ substantially; a 2022 common-year birth denominator cannot establish2026 operation. Cooktown's2022 partial/suspended service and Weipa's2024 reopening need separate scenarios. Cairns can be both an origin and referral service; its referral-only alternative prevents attributing another infant cohort to telephone support. Ten CHHHS and four TCHHS hospital/emergency locations do not exhaust the many primary/community health centres. Adding fixed readiness cost with zero credited consultations is a conservative modelling scenario, not a conclusion that need is zero.

Disposition: explicit roster with missing-versus-zero flags, historical/reopened alternatives, readiness-call and Cairns-referral-only scenarios. Critical infants have no transfer-avoidance effect; baseline transfer0.98 is assumed, not certain. No survival or neurodevelopmental improvement is credited in reference results. EPICure2 utility differences are childhood, proxy-rated, extremely-preterm cohort contrasts; they are not neonatal video effects. Broader language/cultural-access and family displacement consequences remain qualitative. Current capability and routing warrant external clinical review.

## 2. Health-economics and perspective reviewer
Scope: comparator costs, opportunity cost, cash, fiscal transfers, provider allocation, societal boundary, VoP.

Findings: whole-health-system saving cannot be assigned entirely to CHHHS. The receiving share and retrieval payer are unverified. Commonwealth contribution floors are not marginal episode-payment coefficients; caps, prior rates, eligibility and block funding matter. A subsidy shifts payer burden but does not create a societal resource benefit. Patient opportunity time and productivity must not be counted twice. Provider attribution is nested in the system, not another cost to add to it.

Additional reproduced defect: the first draft attributed statewide receiving savings to CHHHS. It was repaired so only CHHHS/TCHHS-origin catchment receiving changes enter that allocation; an unrelated-site invariance regression failed before the fix and now passes.

Additional capital correction: regional retention now removes purchase cost only for the three known pilot installations, not every proposed location; new-site capital remains included. A failing regression demonstrated the issue before repair.

Disposition: component-level provider allocation with receiver share0–1 and a local-only provider scenario; exact ledger reconciliation; fixed-funding reference and explicitly uncapped.405 benchmark-response sensitivity. QEP remains missing. Societal output is labelled bounded health+family resource perspective, not complete education, lifetime NDIS, environment and productivity valuation. VoP uses fixed expected-value choices, explicit tie lottery/bounds, directional regret and network-year units. A zero VoP when perspectives choose the same strategy is retained, not tuned away. Patient-cost ties are not device-equivalence evidence. Full fiscal entitlement and provider revenue forecasts remain unavailable.

## 3. Statistical, evidence and model reviewer
Scope: evidence transportability, distributions, fitting, correlation, sensitivity, outputs.

Findings: no local likelihood has been fitted;4–5 cases have neither complete denominator nor identifiable effect. Beta precision20/Dirichlet concentration20 are judgement, not sample sizes. Scaling then clipping a beta for a changed mean introduces artificial boundary mass. Triangular central values are modes; right-skewed means differ. The air anchor is a lognormal median. Independent input grids are not probability distributions of actual hospitals. Utilities can be negative and should not be forced into beta distributions or equated with1-DW.

Disposition: 49-field parameter audit, non-reference beta reparameterisation with tests, preserved reference v6 sample distribution, common systematic draws across sites/arms, null/sceptical/published structures and deterministic allocation surfaces. Fixed scenario inputs are explicitly separate from PSA. QALY threshold and utility-bridge results are labelled illustrative, with instruments kept separate; DALY arithmetic is not a calibrated DALY result. Four critical neonatal economic/effect papers remain abstract-only. Scientific adequacy is not established by number of tests, PSA iterations or plots.

## 4. Software, privacy and security reviewer
Scope: numerical contracts, clean baseline, dependency policy, caches, source retention, CI, automation and security.

Findings: unrestricted pytest plugin autoload in the shared host stalled an integration test, whereas the exact ordinary suite with third-party autoload disabled completed. The manuscript does not need another runtime framework. The current network cannot install the pinned full stack or download original public source files. Source transcriptions must not masquerade as original files. A regex scan is not Gitleaks, and author-role reviews are not independence.

Additional security repair: redirects are checked against the HTTPS host allowlist before a redirected request is sent. Current assurance paths no longer overwrite v6 receipts. Both have reproducing failure/repair tests.

Disposition: documented ordinary-suite environment, unchanged NumPy core and Polars-only DataFrame policy; explicit source-byte status, SHA256/size manifest and opt-in allowlisted retrieval; minimal restricted ELC excerpt instead of the complete541-page pack. No patient-level data added; no automatic external publishing, code upload or unapproved secret propagation. Actual Gitleaks and external-tool probes are blocked, not passed. Limited redacted text scan is supplementary only. Full lock, populated Conductor, hosted CI and independent review remain open release gates.

## Adjudicated status
Implemented and technically tested: regional exposure overrides; beta repair; perspective reconciliation; tie-aware VoP; health-threshold helpers; exact regional/perspective simulations; source transcriptions and inventory; bounded privacy scan.
Qualified: regional scope and reopening estimates; provider/fiscal attribution; bounded societal result; speculative utility bridge; equal video performance assumptions; standard-price prototypes rather than actual patient grouper output.
Open: current local capability/routing, QEP/weights, invoices/marginal retrieval costs, four critical full texts, all public original source bytes, full external toolchain/Gitleaks, independent clinical/economic review. Simulated role reviews cannot close external-validation items.
