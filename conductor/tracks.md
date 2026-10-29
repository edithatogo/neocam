# Current Conductor tracks — v10

- [Active sequential acceptance/recovery track](tracks/v10-acceptance-reconciliation/plan.md): local repairs and twenty scoped reviews implemented; full acceptance and full GitHub import remain incomplete.
- [Twenty-track reconciliation](reconciliation-v10.md): ordered test counts, remaining requirements and links to the per-track records. Counts overlap and must not be summed.
- [Prior remote v9 track](tracks/v9-reconciliation/plan.md): preserved as a historical record, not overwritten.
- [Current regional/perspective analysis](tracks/v7-perspectives/plan.md): the primary numerical inputs and financial outputs are unchanged. The age-11 utility-generator correction is secondary and historical artifacts are not relabelled as fresh.

Historical index: [v6 and prior](tracks-v6-history.md); [v8 execution](tracks/v8-assurance-publish/plan.md). Each track keeps implementation separate from external acceptance.

Canonical verification: `python -m quality.cli --profile full --evidence-version v10`. Missing tools, unresolved source files, independent review and remote-transfer gaps cannot be marked passed.
