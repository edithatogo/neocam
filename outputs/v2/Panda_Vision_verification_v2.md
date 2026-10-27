# Panda Vision v2 verification — 27 October 2026

## Passed locally
- 75 unit, regression and data tests; no observed failing tests remain.
- 96% branch-inclusive coverage of `src.statewide` (248 statements;80 branches).
- Historical birth reconciliation:72 raw rows,65 combined sites,46,711 public births; pilot486;33-site scenario28,276.
- Fixed-seed reproducibility; source/parameter provenance contracts; immutable action pins and least-privilege checks.
- Workbook formula calculation agrees with Python: programme$14,051.743943848; net resource saving$4,167.437050011. Formula error scan:0 matches.
- Source identifiers in memo/supplement resolved against source/publication registers.
- DOCX rendered: memo2pages; methods/evidence9pages. PowerPoint12slides rendered; final overflow test passed.
- Partial-receipt assurance regression tests:3 failed before implementation, then passed; no partial pipeline receipt is labelled full release assurance.

## Not passed / not executed
- Latest transitive/hash lock resolution failed because external DNS was unavailable. Version targets are recorded, not installed.
- Ruff,Hypothesis,ty and pip-audit unavailable locally; configured online stages are not execution evidence.
- Hosted GitHub Actions and Python3.14/3.15 matrix not run. No deployment performed.
- Conductor gitlink configured/pinned at137c1e41ff9c1dc75ff277b9582460a0bd8c4768; working-tree checkout failed github DNS.
- mchs2026 calculator parity remains unverified; no mchs execution claimed.

## Review and repairs
Author self-review; no independent reviewer. Corrected a rescue-cost test fixture, PSA handling of custom critical-only casemix, a hidden coverage-plugin dependency, partial-assurance metadata, document placeholders, corporate-slide contrast/footer masking and source-reference aliases. Native PowerPoint tables use EMU internally; the original helper's unit mismatch was not an actual overflow. Final rendered/OOXML overflow test passes.

## Boundaries
The case mix, effect transportability, marginal fractions, geography and lifetime extension are researcher assumptions. The literature review is targeted/abstract-based, not a completed systematic full-text review. 2022 site totals are not a certified2026 facility list. Unverified QEP remains missing. Positive modeled net resource savings are not guaranteed budget reductions.

See `verification/assurance.json` for commands/environment/receipts and `outputs/v2/results_v2.json` for model provenance. Workbook edits do not rerun state/PSA snapshots. Full release assurance is false.
