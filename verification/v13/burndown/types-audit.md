# Type-gate work — audit trail (2026-10-31)

Tools: pinned `basedpyright` (`typeCheckingMode=all`, `failOnWarnings`, no config
ignores, no baseline allowed by contract test) and `ty` (`all = "error"`).
No `pyproject.toml` ignore block and no `.basedpyright/baseline.json` was added.

## Results so far

| Scope | basedpyright before → after | ty before → after | Verification |
|---|---|---|---|
| `quality/` | 392 → **0** | 20 → **0** | 68 scoped + 678 full suite; context and workflow gates exit 0 |
| `tests/` | 2,197 → **0** | 28 → **0** | 678 full suite |
| `src/` | 300 → in progress | ~43 → in progress | parity + inputs required |
| nine type-checked scripts | ~820 → in progress (two agents) | in progress | — |

## Independent assertion-integrity audit of the `tests/` type work

Because type work touched 48 test files, the parent re-derived the test surface from
`HEAD` and compared it with the working tree by AST rather than trusting the report:

1. **Assertion multiset and `pytest.raises` signatures** — every `Assert` expression and
   every `pytest.raises(type, match=...)` pair was unparsed and compared per file.
   Result: **0 files changed a `pytest.raises` type or `match=` string**. 21 files show
   textual differences in assertion expressions.
2. **Net assertion counts and tolerance additions** — per file, total `Assert` nodes and
   count of `pytest.approx(..., rel=|abs=)` occurrences, `HEAD` vs working tree.
   Result: only three files lost exactly one assertion each, and **no file gained an
   `approx` tolerance** (0 → 0 everywhere).
3. **The three removed assertions** were `assert importlib.util.find_spec("...")`
   availability checks in `test_v12_artifacts.py`, `test_v12_configuration.py`,
   `test_v12_estate.py`. Each is replaced by a real static import of the same module
   (`from quality import artifacts`, `from src import equipment`, ...), so a missing
   module now fails at import — equal or stronger enforcement, not a relaxation.
4. **Expected values spot-checked**: e.g. `equipment_cost == 20000` is unchanged; the
   expression text differs only because a typed local replaced an inline call.
5. Textual rewrites that are semantically identical: `ndarray.__eq__` replaced by
   `np.equal(...)` (the operator returns `Any` under strict typing), and similar
   cast/narrowing expressions.

Conclusion for `tests/`: no test, assertion, expected value or `pytest.raises` match
string was weakened or removed; the suite count is unchanged at 678 passed.

## Suppression surface added in this phase

- `quality/`: 2 inline `reportPrivateUsage` suppressions (private `_native` resolver and
  the private `_base_arrays` builder), each with a reason.
- `tests/`: 8 inline `reportPrivateUsage` suppressions on in-repo private surfaces under
  test (`_base_arrays`, `_same_value`, `cli._native`, `statewide._odds`), each with a
  reason.
- No file-level or config-level type suppression anywhere.

## Open caveat to re-verify at the end

`src/` and the type-checked scripts were edited concurrently with `tests/`; the
`tests/` agent noted `statewide.evaluate` moved `dict[str, Any]` → `dict[str, object]`
mid-pass. A final whole-project `basedpyright` + `ty` run, plus the full suite, parity
selection and `quality.checks inputs`, must be executed after all edit agents stop.
