# Privacy scan performance: receipt

`quality/privacy.py::scan_repository` walked every line and ran five `re.Pattern.finditer`
passes per line. It now runs each value pattern **once over the whole decoded blob** and
maps each match offset back to its line number. Because every pattern is line-local (no
allowed character is `\n`), whole-blob matching recognises exactly the matches the per-line
walk recognised. A cheap boolean shape predicate precedes each pass (`"@"` for email,
`0[23478]|61` for a telephone that could pass `_is_australian_phone`, the keyword literals
for the Medicare/TFN/card rules), and email is recovered by anchoring at each `@` and
matching the local part that ends there (a mailbox has exactly one `@`, so this is exact).

Measured on this tree (`verification/v13/hosted-41074874950/full/ruff_lint.txt` is 29 MB;
two PDF supplements inflate to ~21-23 MB of stream text each; 185 MB of decoded text total):

| measure | before | after |
| --- | --- | --- |
| full-tree scan (wall) | 15.2 s (parent), 14.8-15.4 s here | 5.17-5.19 s |
| scan, original vs new in one process | 14.609 s | 5.173 s (2.8x) |
| `pytest tests/test_privacy_scan.py` | ~12.5 s (parent) | 5.54 s |
| full suite | ~12.4 s | 11.35 s |

Equivalence was proven in one process: the exact pre-change per-line algorithm is injected
over `_inspect_text`, and both scans run over the same tree. Report bodies are identical,
findings identical (0), `not_scanned` identical (98), counts identical (1527 scanned / 1484
text / 43 container). The tree was stable during the comparison.

Sensitivity is retained: `tests/test_privacy_scan.py` passes (30 tests) and the fixture
still yields all seven rules (`email`, `au_phone`, `medicare_number`, `tfn`, `card_number`,
`identifier_column`, `identifier_key`). Two tests were added for the anchored email path
(64-character local part boundary, several mailboxes on a line) and for line numbering
across a non-newline break.

Gates: `ruff check .` 0 findings; `ruff format --check src scripts quality tests sources`
clean (126 files); `ty check --error-on-warning` clean; `basedpyright` 0 errors;
`pytest -q -p no:cacheprovider` 1087 passed.

**Not reached.** The 2 s target is not met: the floor is full coverage of ~185 MB of
decoded text (a 29 MB generated lint log plus ~70 MB of inflated PDF stream text), which
must each be classified by at least one pattern scan. A candidate-anchored phone scan was
tried and rejected: a non-shape-starting match can shadow an inner passing match, so it
would emit a false positive. The shortfall is reported rather than traded away; no
exemption, scope or bound was relaxed.
