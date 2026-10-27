# Conductor tracks

V3 is an engineering refinement of the v2 model, not a new economic feature release. Implementation and verification are recorded separately; blocked tooling is never a completed acceptance gate.

| Track | Detailed tasks | Status |
|---|---:|---|
| [v3-01-input-and-numerical-integrity](tracks/v3-01-input-and-numerical-integrity/plan.md) | 7 | complete_within_scope |
| [v3-02-dependencies-and-dataframe-policy](tracks/v3-02-dependencies-and-dataframe-policy/plan.md) | 7 | implementation_recorded_acceptance_incomplete |
| [v3-03-solo-assurance-harness](tracks/v3-03-solo-assurance-harness/plan.md) | 8 | implementation_recorded_acceptance_incomplete |
| [v3-04-context-and-ci](tracks/v3-04-context-and-ci/plan.md) | 7 | implementation_recorded_acceptance_incomplete |
| [v3-05-final-verification-and-packaging](tracks/v3-05-final-verification-and-packaging/plan.md) | 5 | implementation_recorded_acceptance_incomplete |

Each active track retains its specification, granular plan and machine-readable task metadata. Across the five tracks there are 34 tasks, with file-level scope, executable acceptance commands and evidence paths. Historical v1/v2 tracks remain in the repository.

Begin with `current-state.json` and `runbook.md`. The next unresolved acceptance step is genuine lock resolution and isolated installation, followed by the same full harness used in CI. No additional clinical information or structured elicitation is a prerequisite.
