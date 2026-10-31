# Execution ledger — v14-03 ecosystem integration

3.1 Inventory — not started. Known material from the reconnaissance in
`conductor/v14-design.md` and `docs/library-integration.md`:

- Already incorporated: `neocam` itself; `edithatogo/conductor-next` as the pinned
  submodule (`extensions/conductor`, pinned 137c1e41).
- Already documented as deliberate external references: `vop_poc_nz` (method contract
  reimplemented from the inspected commit ad84d30), `mchs` (checked 9fc8d0f, not
  executed), `microcosting_healthworkforce`, `voiage` (deferred).
- Candidates not yet incorporated, with the reason they matter: `template-solo-data`
  (reusable CI/Renovate/OIDC pattern), `careops-rims` (real `privacy.yml` plus secret
  and privacy safeguards), `sourceright` (citation/reference verification, mapping onto
  `sources/` and the citation receipts), `riopa-infrastructure` (provenance-first
  reproducible-research infrastructure).
- Owner decision required per repository: pinned submodule, documented reference, real
  dependency, or CI reuse. Nothing is added before that decision.

3.2–3.3 privacy patterns and CI alignment — not started.

3.4 Canonical VoI alignment with `voiage`/`vop_poc_nz` — GATED. The repository states
"`voiage` deferred until decision utility is credible; current EVPI is explicitly
cost-only". No work starts until the owner confirms credibility; if it proceeds it is a
model track with its own parity suite, because results may legitimately change.
