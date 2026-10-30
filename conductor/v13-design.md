# V13 bounded decision refinements

## Accepted scope
The user authorised the four further refinements and their implementation/review. No new measured effects, device approvals, local incidence estimates, additional clinical data collection or larger architecture are introduced.

## 1. Denominators
`ActivitySpec(activity_basis, contacts_per_episode)` separates forecast contacts from episodes. For fixed forecast contacts, episodes=forecast/contacts_per_episode. For fixed episodes, contacts=forecast*contacts_per_episode. Outcomes use episodes once; video workflow uses contacts. Same contact intensity applies to telephone and video; episode-level video reliability is unchanged. The legacy `consultations` output is retained as an explicitly documented alias for episodes, with new `episodes` and `contacts` fields. Multiplier 1 preserves reference values. No claim that one episode always equals one unique infant across repeated illness episodes.

## 2. Eligibility and deployment
Named `DeploymentPolicy` assigns exactly one strategy per site. Eligibility records distinguish reported current operation, hypothetical suitability and unknown. Never infer approval for a new location or device from a technology category. Actual reported-policy set: telephone throughout; retain Panda at three reported pilot sites with telephone elsewhere. Expansion policies are conditional scenarios only. Reject unknown/duplicate/missing assignments and unapproved options in strict mode.
Aggregate exact per-site clinical/cost components on paired draws. Sum specialist hours first and apply the shared hub's spare-capacity/block rule once, not once per equipment group. Use the same estate and contact assumptions for resource and seven-year cash calculations. Evaluate health-system and bounded societal resources only in the supplemental policy comparison; existing six-perspective v12 results remain separately authoritative. Extending provider fiscal allocation to arbitrary policies needs its own explicit hub/destination agreement and is not fabricated here.

## 3. Plausibility and evidence
Generate review-ready absolute counts, ratios, workload and incremental costs. Automatic conservation/finite/unit checks are not clinical approval. Review records require role, identity, independent status, exact snapshot, conflict statement, findings and resolutions; blank/pending records fail release acceptance. Prior-predictive comparison is not fitting to 4–5 cases. Extra appropriate transfers are reported separately and never coded as automatically harmful.
Keep a blocker registry for four core full texts, original sources, lock/tool/security acceptance, submodule, remote migration and independent review. It records evidence and executable next actions, not invented completion.

## 4. Delivery
Add no Python runtime dependencies. A new `config/refinements.json` contains scenario multipliers 1,1.5,2 and labels them analyst sensitivity settings. The new driver consumes the existing validated reference configuration plus this file, emits paired PSA summaries, deterministic results, predictive rows, policy eligibility/assignments and budgets, and a separate manifest. No existing output overwritten. Scope-wide review and tests before final frozen receipt. Private PR #3 receives verified source changes; remote completeness is separately checked.

## Risks
Contacts correlated with severity not identified; no per-contact repeated probability of clinical success. Historical birth proxies/capability/routing unchanged. Current pilot operation is not a medical-device or site approval certificate. No new causal HRQoL/mortality estimate or mathematical optimisation over all sites. Cost-only choice is conditional on clinical suitability and cannot settle safety.
