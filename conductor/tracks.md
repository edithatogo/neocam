# Current Conductor tracks

- [Sequential acceptance and recovery](tracks/v10-acceptance-reconciliation/plan.md): repairs and twenty historical scoped reviews; source/history import and full external acceptance remain incomplete.
- [Twenty-track reconciliation](reconciliation-v10.md): ordered test counts and remaining requirements. Counts overlap; do not sum them as independent tests.
- [Concurrent revalidation work](tracks/v10-revalidation/plan.md): retained as separately recorded work; not overwritten or merged into a claim of independent validation.
- [Prior v9 reconciliation](tracks/v9-reconciliation/plan.md): historical work preserved.

Canonical execution: `python -m quality.cli --profile full --evidence-version v10`. A finished run is not a passed run. Missing tools, critical full texts, original-source downloads, independent review and untransferred files remain open.
