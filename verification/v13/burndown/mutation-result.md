# Mutation gate: authoritative full run (2026-10-31)

Command (identical to the harness gate `quality/cli.py`):

```
uv run --frozen --no-sync python -m pytest -p gremlins tests quality/hypothesis_properties.py \
  --gremlins --gremlin-workers=2 --gremlin-clear-cache \
  --gremlin-report=json --gremlin-report=html --strict-pardons
```

## Result — gate PASSED

| Metric | Value |
|---|---|
| total mutants | 1,250 |
| zapped | **1,244** |
| survived | **6** |
| timeout | **0** |
| error | **0** |
| pardoned | **0** |
| score | **99.52%** (floor is 90%) |
| gate verdict | `python -m quality.checks mutation` → `{"check": "mutation", "errors": []}` (exit 0) |

Suite at time of run: 1,034 tests, 412s wall clock on 2 workers.

Baseline for comparison: the hosted run on commit 4bdb86b measured 903/1,294 = **69.78%**
with 391 survivors (`mutation-survivors.md` is that target list).

## The six survivors

Four are provably equivalent mutants and cannot be killed by any test:

| Location | Mutation | Why it cannot be killed |
|---|---|---|
| `quality/assurance.py:114` | `text=True` → `False` | the same call passes `encoding=`, so CPython forces text mode regardless |
| `quality/contracts.py:157` | `zip(strict=True)` → `False` | only reached after a length-equality check short-circuits |
| `src/pathways_v6.py:92` | `copy=False` → `True` | no public path aliases the returned buffer, so the flag is unobservable |
| `src/sensitivity.py:196` | `<=` → `<=` | bytecode-identical no-op emitted by the tool |

Two are genuine remaining survivors:

| Location | Mutation | Note |
|---|---|---|
| `src/statewide.py:500` | `>` → `>=` (comparison) | not killed; a boundary test discriminating the endpoints would be needed |
| `src/statewide.py:500` | boundary shift ±1 | same site |

Per-group outcome (scoped runs by the four mutation agents, each with its own
`--gremlin-targets`): deployment 23→0, portfolios_v7 24→0, strategies 16→0, pathways_v6
56→1, sensitivity 24→1, audit_v7 24→0, perspectives_v7 15→0, configuration 14→0,
equipment 12→0, activity 2→0, quality/assurance 12→1, quality/contracts 3→1,
statewide.py 163→2.

## Why the score is measured by one full run

Scoped runs are useful per module, but the gate reads the single summary written by the
last complete run, and `quality.checks mutation` reconciles `total = zapped + survived +
timeout + error + pardoned` and requires the reported percentage to match the counts to
within 0.02. Summing scoped percentages would overstate the score, so the authoritative
number above comes from the un-scoped command.

## Note on the 3.15 warning risk

The full run recorded **0 errors**, so the intermittent pytest tmp-cleanup
ResourceWarning discussed in `python-policy.md` did not affect the gate. `filterwarnings
= ["error"]` remains untouched.
