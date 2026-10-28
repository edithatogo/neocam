# Panda Vision v5 — comparative model, sensitivity and publication handoff

28 October 2026. Preliminary existing-evidence economic model; not procurement approval, clinical validation or a production release.

## What was implemented

Five complete service configurations now share the existing severity-stratified numerical kernel: telephone, mobile teleconference, Panda Vision, ceiling/wall PTZ and a complete tablet/OBSBOT kit. Telephone consultation remains common care. Existing Panda deterministic and paired PSA outputs are reproduced exactly. The original 27 model parameters and nine protected scientific/evidence files are unchanged. New comparator prices, capital attribution and prototype delivery/cost assumptions are separately registered, not represented as observations.

Reference clinical effect and usable delivery are the same across video configurations as an explicit hypothesis, not established equivalence. Full procurement cash, neonatal attribution and sunk equipment are distinguished. Eligibility-restricted outputs exclude the prototype until technical approval. All reported rankings and decision surfaces come from the exact model, not machine learning.

## Executed analysis

- 18 paired PSA structures, each with 20,000 draws and five configurations; six additional independent-seed runs.
- Twelve one-way dimensions at 21 points for pilot and state portfolios: 2,520 arm-level rows.
- Four complete two-way pairs at 31 by 31 for both portfolios: 7,688 exact design points.
- An exact selected five-way grid with 3,125 points and a prespecified equipment four-way grid with 2,401 points.
- Independent 12-dimensional design: 8,192 train, 2,048 selection and 4,096 fresh test points. Input-only clustering is weak/unstable and is not a discovered patient or hospital typology.
- Sobol first/total-order analysis at two base sizes, 86,016 design evaluations across six outcomes. Independent uniform sensitivity ranges are not the correlated PSA distribution.
- Held-out decision classifier agreement 95.0%, balanced agreement 93.3%, mean exact-model decision regret AUD60 and worst AUD8,970 per pilot-year. Predictive importance is not a causal effect or EVPPI. A shallow tree is expressly unsuitable as a decision rule.
- Earlier scenarios, survival/morbidity and funding/budget analyses remain in the repository; they are not relabelled as five-device clinical evidence.

## Decisions depend on the question

Under equal-video/new-purchase assumptions the complete kit is mechanically preferred among video options. Retaining already-installed Panda changes the choice. Uncertain prototype cost and usable delivery change pilot and state rankings. Probability of being cost-optimal is not expected net value or probability of better clinical care. Costs and results remain assumption-dependent; QEP, invoices, local marginal retrieval costs and clinical effects retain uncertainty.

## Actual verification

- Final ordinary covered suite: **379 passed**, with no observed test failure remaining.
- Scoped combined statement/branch coverage: **94.63%**. All four numerical modules have 100% in the recorded scope. Research-orchestration and artifact generation scripts are not implied to have this coverage.
- Full requested harness: **6 passed, 22 blocked, 1 failed**. Full acceptance remains unsuccessful.
- The missing real uv.lock fails dependency consistency. Required external tools/latest-version installation, actual Conductor checkout and hosted CI remain incomplete. Missing tools are never a pass.
- Source commit for final harness: `7ce98c6c058c716b8efa7cf8a1e98f59185198d2`.
- Input fingerprint: `07c85eeddabdcc7c234b74aa2dbc138c031f732f5825716cc672887028db4a60`.
- Final runtime: Python3.13.5, NumPy2.3.5, SciPy1.17.0, scikit-learn1.8.0. New optional targets SciPy1.18.1/scikit-learn1.9.1 were verified but not installed. Full CI now installs and version-checks the research extra. Polars-only DataFrame policy retained; no pandas/xarray project import or dependency added. Full isolated transitive dependency absence is not certified without a resolved lock.

## Repairs and review boundary

Final full-suite testing exposed five stale v4 integration-fixture paths, now migrated to the current evidence paths. A failing regression prompted network-free bounded acceptance checking with `uv lock --check --offline`; lock resolution remains a distinct connected maintenance action. Missing locks still fail. New optional research dependencies initially did not enter the inherited install/version contract; two failing regressions were corrected. A misleading five-way figure title was corrected because that particular fixed-prototype slice has only four winners. Initial weak cost-regression decision accuracy was not concealed: a decision classifier was selected on a separate selection set, then evaluated on a fresh independent holdout without retuning.

One analysis call and two full harness attempts were interrupted by the execution environment. Those logs remain labelled interrupted. The completed rerun produced the results and final receipt above. No runtime speedup is inferred from interruptions or one timing.

Review was by the author, not an independent reviewer. Full-text source verification, independent clinical/economic structural review and connected clean release acceptance remain open. No new recruitment or formal expert elicitation is required to undertake this model-based evaluation.

## Artifact checks

Two-page CHHHS plan and eleven-page supplement were rendered; every document page was visually reviewed. Twelve CHHHS slides were rendered and reviewed, with no detected slide overflow. Fifteen separate PNG/SVG figures and all raw CSV tables are included. The 18-sheet workbook contains50 checked/cached formulas and no detected formula-error cells; it is an inspectable results workbook, not a spreadsheet PSA engine. Counts/hashes/formula checks are in artifact_audit.json and outputs/v5/analysis_manifest.json.

Three new Conductor tracks contain18 detailed tasks, with implementation distinct from connected acceptance. The reusable lean-CI skill is preserved. The Conductor gitlink remains unpopulated. No journal was contacted, no submission made, no GitHub push or deployment performed. Do not publish restricted ELC/corporate assets without permission.
