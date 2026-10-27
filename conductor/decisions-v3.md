# V3 decisions

- Interpret “Polaris” as Polars, the DataFrame library. No pandas/xarray imports or resolved dependencies are permitted.
- Do not introduce a new modelling framework. Keep the existing NumPy cohort kernel and standard-library CSV contracts. Polars is an optional tabular adapter, not a prerequisite for numerical calculations.
- Latest means the latest non-yanked published release verified from a primary source. Preview diagnostics are enabled for Ruff; no source-built compiler/runtime stack.
- No forced structured elicitation. Assumptions remain assumptions, with provenance and uncertainty recorded.
- Use isolated branch conductor/panda-vision-v3-assurance. No remote destination was authorised; do not push or create a public repository.
- External DNS/download attempts failed in this runtime. Target pins cannot be described as installed or fully tested.
- Preserve historical artifacts and Git history; report code-level assurance separately from clinical or economic validity.
