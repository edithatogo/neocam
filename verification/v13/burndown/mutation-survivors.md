# Mutation survivors — hosted run 41082033781 (commit 4bdb86b)

Score at that commit: 903/1294 = 69.78% (391 survived, 0 timeouts, 0 errors, 0 pardons).
Target: 90% => at most 129 survivors of 1,294; at least 262 survivors must be killed.

Line numbers are from the hosted commit. The formatting/typing burn-down has since shifted some
lines, so locate each gremlin by its operator + description in the current file.

## neocam/src/statewide.py — 163 survivors

| line | operator | mutation |
|---|---|---|
| 25 | boolean | True to False |
| 40 | comparison | <= to < |
| 40 | comparison | <= to <= |
| 40 | boundary | boundary shift +/-1 |
| 40 | boundary | boundary shift +/-1 |
| 40 | boundary | boundary shift +/-1 |
| 40 | boundary | boundary shift +/-1 |
| 50 | boolean | True to False |
| 107 | boundary | boundary shift +/-1 |
| 107 | boolean | and to or |
| 111 | comparison | <= to < |
| 111 | comparison | <= to <= |
| 111 | boundary | boundary shift +/-1 |
| 113 | comparison | <= to < |
| 113 | comparison | <= to <= |
| 139 | comparison | < to <= |
| 139 | boundary | boundary shift +/-1 |
| 139 | boundary | boundary shift +/-1 |
| 155 | comparison | < to <= |
| 155 | boundary | boundary shift +/-1 |
| 155 | boundary | boundary shift +/-1 |
| 157 | comparison | >= to > |
| 157 | comparison | >= to < |
| 157 | boundary | boundary shift +/-1 |
| 157 | boundary | boundary shift +/-1 |
| 173 | comparison | == to != |
| 175 | comparison | == to != |
| 187 | boundary | boundary shift +/-1 |
| 193 | boundary | boundary shift +/-1 |
| 200 | comparison | < to <= |
| 200 | boundary | boundary shift +/-1 |
| 219 | arithmetic | * to / |
| 227 | arithmetic | - to + |
| 242 | comparison | == to != |
| 243 | arithmetic | * to / |
| 243 | arithmetic | / to * |
| 243 | arithmetic | * to / |
| 243 | arithmetic | * to / |
| 243 | arithmetic | * to / |
| 243 | arithmetic | * to / |
| 243 | arithmetic | * to / |
| 255 | arithmetic | * to / |
| 255 | arithmetic | * to / |
| 255 | arithmetic | * to / |
| 255 | arithmetic | + to - |
| 256 | arithmetic | * to / |
| 256 | arithmetic | * to / |
| 258 | arithmetic | + to - |
| 258 | arithmetic | * to / |
| 261 | comparison | > to >= |
| 261 | comparison | > to < |
| 261 | boundary | boundary shift +/-1 |
| 261 | boundary | boundary shift +/-1 |
| 262 | arithmetic | / to * |
| 263 | arithmetic | * to / |
| 264 | arithmetic | * to / |
| 264 | arithmetic | * to / |
| 264 | arithmetic | + to - |
| 264 | arithmetic | + to - |
| 264 | arithmetic | + to - |
| 271 | arithmetic | * to / |
| 272 | boundary | boundary shift +/-1 |
| 273 | arithmetic | - to + |
| 273 | arithmetic | / to * |
| 275 | arithmetic | * to / |
| 275 | arithmetic | + to - |
| 279 | arithmetic | + to - |
| 297 | comparison | < to <= |
| 297 | boundary | boundary shift +/-1 |
| 297 | comparison | > to >= |
| 297 | boundary | boundary shift +/-1 |
| 304 | arithmetic | * to / |
| 305 | arithmetic | - to + |
| 305 | arithmetic | * to / |
| 305 | arithmetic | / to * |
| 309 | comparison | == to != |
| 309 | comparison | == to != |
| 311 | arithmetic | * to / |
| 313 | arithmetic | * to / |
| 313 | arithmetic | ** to * |
| 313 | arithmetic | ** to * |
| 315 | comparison | < to <= |
| 315 | comparison | < to > |
| 315 | comparison | < to < |
| 315 | comparison | < to < |
| 315 | boundary | boundary shift +/-1 |
| 315 | boundary | boundary shift +/-1 |
| 315 | boundary | boundary shift +/-1 |
| 315 | boundary | boundary shift +/-1 |
| 315 | comparison | < to <= |
| 315 | comparison | < to > |
| 315 | boundary | boundary shift +/-1 |
| 315 | boundary | boundary shift +/-1 |
| 315 | boolean | and to or |
| 315 | arithmetic | * to / |
| 315 | arithmetic | - to + |
| 315 | arithmetic | * to / |
| 318 | comparison | > to >= |
| 318 | boundary | boundary shift +/-1 |
| 320 | arithmetic | * to / |
| 321 | arithmetic | / to * |
| 323 | arithmetic | / to * |
| 323 | arithmetic | * to / |
| 324 | arithmetic | * to / |
| 324 | arithmetic | / to * |
| 325 | arithmetic | * to / |
| 326 | arithmetic | * to / |
| 327 | arithmetic | * to / |
| 327 | arithmetic | / to * |
| 329 | arithmetic | - to + |
| 329 | arithmetic | + to - |
| 330 | arithmetic | * to / |
| 330 | arithmetic | / to * |
| 331 | arithmetic | * to / |
| 331 | arithmetic | / to * |
| 332 | arithmetic | * to / |
| 332 | arithmetic | / to * |
| 333 | arithmetic | * to / |
| 333 | arithmetic | / to * |
| 334 | arithmetic | * to / |
| 334 | arithmetic | / to * |
| 335 | arithmetic | * to / |
| 335 | arithmetic | / to * |
| 336 | arithmetic | * to / |
| 336 | arithmetic | / to * |
| 337 | arithmetic | * to / |
| 354 | comparison | > to >= |
| 354 | comparison | > to < |
| 354 | boundary | boundary shift +/-1 |
| 354 | boundary | boundary shift +/-1 |
| 356 | arithmetic | - to + |
| 360 | arithmetic | - to + |
| 360 | arithmetic | * to / |
| 360 | arithmetic | / to * |
| 380 | comparison | < to <= |
| 380 | boundary | boundary shift +/-1 |
| 380 | boundary | boundary shift +/-1 |
| 380 | comparison | <= to < |
| 380 | boundary | boundary shift +/-1 |
| 380 | boundary | boundary shift +/-1 |
| 380 | comparison | < to <= |
| 380 | boundary | boundary shift +/-1 |
| 382 | comparison | <= to < |
| 382 | comparison | <= to <= |
| 382 | boundary | boundary shift +/-1 |
| 384 | comparison | < to <= |
| 384 | boundary | boundary shift +/-1 |
| 386 | arithmetic | + to - |
| 386 | arithmetic | + to - |
| 389 | arithmetic | * to / |
| 389 | arithmetic | - to + |
| 389 | arithmetic | * to / |
| 389 | arithmetic | * to / |
| 390 | arithmetic | * to / |
| 390 | arithmetic | - to + |
| 390 | arithmetic | * to / |
| 390 | arithmetic | + to - |
| 390 | arithmetic | * to / |
| 394 | boolean | True to False |
| 396 | comparison | < to <= |
| 396 | boundary | boundary shift +/-1 |
| 403 | arithmetic | + to - |
| 405 | arithmetic | - to + |

## neocam/src/pathways_v6.py — 56 survivors

| line | operator | mutation |
|---|---|---|
| 26 | boolean | True to False |
| 52 | comparison | > to >= |
| 54 | boundary | boundary shift +/-1 |
| 65 | boolean | False to True |
| 70 | boundary | boundary shift +/-1 |
| 70 | boundary | boundary shift +/-1 |
| 70 | boolean | or to and |
| 114 | arithmetic | - to + |
| 120 | comparison | > to >= |
| 120 | comparison | > to < |
| 120 | boundary | boundary shift +/-1 |
| 120 | boundary | boundary shift +/-1 |
| 146 | comparison | == to != |
| 147 | arithmetic | * to / |
| 147 | arithmetic | / to * |
| 147 | arithmetic | * to / |
| 147 | arithmetic | * to / |
| 147 | arithmetic | * to / |
| 147 | arithmetic | * to / |
| 147 | arithmetic | * to / |
| 151 | arithmetic | / to * |
| 152 | comparison | > to >= |
| 152 | boundary | boundary shift +/-1 |
| 181 | boundary | boundary shift +/-1 |
| 199 | arithmetic | * to / |
| 200 | arithmetic | * to / |
| 248 | arithmetic | * to / |
| 250 | arithmetic | + to - |
| 253 | boundary | boundary shift +/-1 |
| 254 | arithmetic | / to * |
| 272 | boolean | and to or |
| 281 | arithmetic | - to + |
| 282 | arithmetic | - to + |
| 285 | arithmetic | * to / |
| 286 | arithmetic | + to - |
| 297 | arithmetic | / to * |
| 297 | arithmetic | * to / |
| 298 | arithmetic | / to * |
| 298 | arithmetic | * to / |
| 299 | arithmetic | ** to * |
| 299 | arithmetic | * to / |
| 299 | arithmetic | * to / |
| 300 | arithmetic | * to / |
| 301 | arithmetic | * to / |
| 307 | boolean | False to True |
| 311 | comparison | < to <= |
| 311 | boundary | boundary shift +/-1 |
| 311 | comparison | < to <= |
| 311 | boundary | boundary shift +/-1 |
| 314 | comparison | > to >= |
| 316 | comparison | != to == |
| 316 | boolean | and to or |
| 321 | arithmetic | % to // |
| 321 | boolean | and to or |
| 323 | arithmetic | + to - |
| 324 | arithmetic | + to - |

## neocam/src/audit_v7.py — 24 survivors

| line | operator | mutation |
|---|---|---|
| 18 | comparison | <= to < |
| 18 | boundary | boundary shift +/-1 |
| 18 | boundary | boundary shift +/-1 |
| 18 | comparison | < to <= |
| 18 | boundary | boundary shift +/-1 |
| 18 | boundary | boundary shift +/-1 |
| 18 | boolean | or to and |
| 32 | comparison | != to == |
| 35 | comparison | != to == |
| 42 | comparison | <= to < |
| 42 | boundary | boundary shift +/-1 |
| 42 | boundary | boundary shift +/-1 |
| 50 | boolean | or to and |
| 52 | comparison | < to <= |
| 52 | boundary | boundary shift +/-1 |
| 52 | boundary | boundary shift +/-1 |
| 52 | comparison | > to < |
| 52 | boundary | boundary shift +/-1 |
| 52 | comparison | > to >= |
| 52 | boundary | boundary shift +/-1 |
| 52 | comparison | < to <= |
| 52 | boundary | boundary shift +/-1 |
| 52 | boundary | boundary shift +/-1 |
| 52 | boolean | or to and |

## neocam/src/deployment.py — 24 survivors

| line | operator | mutation |
|---|---|---|
| 18 | boolean | True to False |
| 34 | boolean | True to False |
| 40 | boolean | False to True |
| 43 | boolean | or to and |
| 46 | boolean | or to and |
| 49 | boolean | or to and |
| 50 | boolean | or to and |
| 56 | boolean | False to True |
| 78 | boolean | or to and |
| 81 | boolean | or to and |
| 125 | boolean | True to False |
| 132 | boolean | or to and |
| 161 | comparison | > to >= |
| 161 | boundary | boundary shift +/-1 |
| 161 | boundary | boundary shift +/-1 |
| 189 | comparison | <= to < |
| 189 | comparison | <= to <= |
| 189 | boundary | boundary shift +/-1 |
| 189 | boundary | boundary shift +/-1 |
| 189 | boundary | boundary shift +/-1 |
| 189 | boundary | boundary shift +/-1 |
| 189 | boolean | or to and |
| 201 | arithmetic | + to - |
| 205 | arithmetic | + to - |

## neocam/src/portfolios_v7.py — 24 survivors

| line | operator | mutation |
|---|---|---|
| 15 | comparison | == to != |
| 17 | comparison | == to != |
| 18 | comparison | == to != |
| 37 | boolean | False to True |
| 38 | boolean | False to True |
| 46 | comparison | < to > |
| 46 | boundary | boundary shift +/-1 |
| 46 | comparison | < to <= |
| 46 | boundary | boundary shift +/-1 |
| 46 | boundary | boundary shift +/-1 |
| 46 | boolean | or to and |
| 50 | comparison | == to != |
| 50 | boolean | and to or |
| 51 | boolean | and to or |
| 52 | comparison | == to != |
| 53 | arithmetic | * to / |
| 53 | arithmetic | / to * |
| 53 | arithmetic | * to / |
| 53 | arithmetic | * to / |
| 53 | arithmetic | * to / |
| 54 | comparison | == to != |
| 55 | arithmetic | / to * |
| 55 | arithmetic | * to / |
| 55 | arithmetic | + to - |

## neocam/src/sensitivity.py — 24 survivors

| line | operator | mutation |
|---|---|---|
| 10 | boolean | True to False |
| 46 | boundary | boundary shift +/-1 |
| 56 | boundary | boundary shift +/-1 |
| 59 | comparison | < to <= |
| 59 | comparison | > to >= |
| 77 | comparison | <= to < |
| 77 | comparison | <= to <= |
| 77 | boundary | boundary shift +/-1 |
| 77 | boundary | boundary shift +/-1 |
| 102 | arithmetic | - to + |
| 125 | comparison | > to >= |
| 125 | boundary | boundary shift +/-1 |
| 125 | boundary | boundary shift +/-1 |
| 136 | comparison | < to <= |
| 136 | boundary | boundary shift +/-1 |
| 136 | boundary | boundary shift +/-1 |
| 140 | comparison | == to != |
| 142 | comparison | <= to < |
| 142 | boundary | boundary shift +/-1 |
| 142 | boundary | boundary shift +/-1 |
| 143 | comparison | <= to < |
| 143 | comparison | <= to > |
| 143 | boundary | boundary shift +/-1 |
| 143 | boundary | boundary shift +/-1 |

## neocam/src/strategies.py — 18 survivors

| line | operator | mutation |
|---|---|---|
| 15 | boolean | True to False |
| 26 | boolean | True to False |
| 27 | boolean | False to True |
| 29 | boolean | False to True |
| 50 | boundary | boundary shift +/-1 |
| 50 | boundary | boundary shift +/-1 |
| 114 | comparison | < to <= |
| 114 | boundary | boundary shift +/-1 |
| 122 | comparison | > to >= |
| 122 | comparison | > to < |
| 122 | boundary | boundary shift +/-1 |
| 122 | boundary | boundary shift +/-1 |
| 131 | arithmetic | + to - |
| 132 | arithmetic | - to + |
| 134 | comparison | > to >= |
| 134 | comparison | > to < |
| 134 | boundary | boundary shift +/-1 |
| 134 | boundary | boundary shift +/-1 |

## neocam/src/perspectives_v7.py — 15 survivors

| line | operator | mutation |
|---|---|---|
| 14 | boundary | boundary shift +/-1 |
| 14 | boundary | boundary shift +/-1 |
| 21 | boolean | True to False |
| 22 | boolean | True to False |
| 40 | comparison | > to >= |
| 40 | comparison | > to < |
| 40 | boundary | boundary shift +/-1 |
| 40 | boundary | boundary shift +/-1 |
| 40 | comparison | > to >= |
| 40 | comparison | > to < |
| 40 | boundary | boundary shift +/-1 |
| 40 | boundary | boundary shift +/-1 |
| 42 | arithmetic | - to + |
| 43 | arithmetic | - to + |
| 57 | boolean | or to and |

## neocam/src/configuration.py — 14 survivors

| line | operator | mutation |
|---|---|---|
| 37 | boolean | True to False |
| 71 | boolean | or to and |
| 74 | boolean | or to and |
| 96 | comparison | <= to < |
| 96 | comparison | <= to <= |
| 96 | boundary | boundary shift +/-1 |
| 96 | boundary | boundary shift +/-1 |
| 96 | boundary | boundary shift +/-1 |
| 96 | boundary | boundary shift +/-1 |
| 96 | boolean | or to and |
| 98 | comparison | < to <= |
| 98 | boundary | boundary shift +/-1 |
| 105 | comparison | > to >= |
| 108 | boolean | True to False |

## neocam/quality/assurance.py — 12 survivors

| line | operator | mutation |
|---|---|---|
| 21 | boolean | True to False |
| 35 | boolean | and to or |
| 41 | boolean | True to False |
| 62 | boolean | True to False |
| 72 | boolean | True to False |
| 79 | boolean | True to False |
| 86 | comparison | != to == |
| 86 | boundary | boundary shift +/-1 |
| 86 | boundary | boundary shift +/-1 |
| 103 | arithmetic | - to + |
| 125 | comparison | < to <= |
| 144 | boolean | and to or |

## neocam/src/equipment.py — 12 survivors

| line | operator | mutation |
|---|---|---|
| 12 | boolean | True to False |
| 23 | comparison | <= to <= |
| 23 | boundary | boundary shift +/-1 |
| 23 | boundary | boundary shift +/-1 |
| 40 | boundary | boundary shift +/-1 |
| 65 | boolean | True to False |
| 73 | comparison | < to <= |
| 73 | boundary | boundary shift +/-1 |
| 79 | comparison | > to >= |
| 92 | arithmetic | + to - |
| 93 | comparison | != to == |
| 94 | boolean | and to or |

## neocam/quality/contracts.py — 3 survivors

| line | operator | mutation |
|---|---|---|
| 85 | boolean | and to or |
| 86 | boolean | True to False |
| 89 | boolean | and to or |

## neocam/src/activity.py — 2 survivors

| line | operator | mutation |
|---|---|---|
| 10 | boolean | True to False |
| 35 | boolean | True to False |

