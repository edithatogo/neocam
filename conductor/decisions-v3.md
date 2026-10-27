# V3 decisions

- Interpret “Polaris” as Polars, the DataFrame library. No pandas/xarray imports or resolved dependencies are permitted.
- Do not introduce a new modelling framework. Keep the existing NumPy cohort kernel and standard-library CSV contracts. Polars is an optional tabular adapter, not a prerequisite for numerical calculations.
- Latest means the latest non-yanked published release verified from a primary source. Preview diagnostics are enabled for Ruff; no source-built compiler/runtime stack.
- No forced structured elicitation. Assumptions remain assumptions, with provenance and uncertainty recorded.
- Use isolated branch conductor/panda-vision-v3-assurance. No remote destination was authorised; do not push or create a public repository.
- External DNS/download attempts failed in this runtime. Target pins cannot be described as installed or fully tested.
- Preserve historical artifacts and Git history; report code-level assurance separately from clinical or economic validity.

- Audit correction: the model has 27 parameter fields, not 28. All 27 are represented in the JSON and evidence register. The earlier 28-field planning description was incorrect; the schema and register both contain 27 parameters. No extra parameter is introduced to satisfy an incorrect count.
- pytest-gremlins current documentation no longer documents a `min_score` configuration key. The full gate will parse its generated JSON and enforce a 90% mutation score, reject zero-mutant reports and fail on mutation errors/timeouts. The threshold is an acceptance target, not an achieved score.

- Integrity failures (bad archive digest, unsafe source or oversized artifact) are failed checks, not dependency-unavailability excuses. Only a declared prerequisite may use exit 69 to report a blocker.
- Native release identities are checked separately from binary digests; a different PATH binary cannot silently satisfy the target version.
- The resolver itself is pinned in the assurance environment and CI bootstrap. Ordinary CI uses frozen installations and never upgrades the lock.
- Scalene uses its CPU-and-memory profiling mode; no AI profiling assistant or code upload is invoked.
- Shared-host tests must simulate environment identity rather than rely on this container's path. A test that passes only outside CI is not acceptable.
- Keep the external mchs calculator at an import/export boundary until its year-specific parity and pandas-free dependency compatibility are demonstrated. Do not import its pandas runtime.
- Broad Ruff ALL/preview and two strict type checkers are configured but not accepted: their first real execution may require code-style/type repairs. No generated ignore-all baseline is supplied.
- Historical document/spreadsheet/slide generation is deliberately not expanded or rebuilt. Default economic results and protected inputs are verified unchanged.
