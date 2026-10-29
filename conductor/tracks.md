# Current Conductor tracks

- [v11 scoped repairs and recovery](tracks/v11-executable-recovery/plan.md): three tested assurance repairs; complete test-tree recovery; full external acceptance remains open.
- [22-track sequential reconciliation](../handoff/v11/tracks.md): original twenty tracks followed by both v10 records. Scoped counts overlap and are not independent test counts.
- [Prior acceptance reconciliation](tracks/v10-acceptance-reconciliation/plan.md) and [concurrent revalidation](tracks/v10-revalidation/plan.md): preserved, not treated as independent validation.

Canonical command: `python -m quality.cli --profile full --evidence-version v11`. All required gates remain mandatory. A finished run is not a passed run. PR #3 remains draft and the complete file/history migration remains open.
