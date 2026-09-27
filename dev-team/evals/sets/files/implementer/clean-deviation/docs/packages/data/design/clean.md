Mode: new

# Design — `data/clean`

Written 2026-09-24 by `dev-team:designer`. Run: `run-package data`.

## 1. Purpose and scope

Turns the rows `ingest` reads into a **TradeTable**: exact duplicate rows collapse to one, the
result is sorted by `ts` then `symbol`. Owns nothing else — no parsing, no persistence, no
validation beyond what the row type already guarantees.

## 2. Inputs and outputs

| direction | name | type | from / to |
|---|---|---|---|
| in | `rows` | `list[Trade]` | `data/ingest` — `load_trades` (`packages/data/src/data/ingest/README.md`, Entry points) |
| out | the table | `list[Trade]` — a **TradeTable** (`docs/architecture.md`, Boundaries) | `data/storage`, the `daily` pipeline |

`Trade` is `data.ingest.Trade`; this section defines no row type of its own.

## 3. Data model / internal contracts

No state, no tables, no settings (`configs.py` is not needed; the section has no
configuration).

**Module plan** — under `packages/data/src/data/clean/`:

| file | holds | defines (§5) |
|---|---|---|
| `__init__.py` | re-exports `clean_trades`, `CleanError` | — |
| `rules.py` | `clean_trades`; `_dedupe(rows: list[Trade]) -> list[Trade]` — collapses exact duplicates with `set(rows)`: `Trade` is a frozen dataclass, so two rows with equal fields hash equal and the set keeps one; `_sort(rows: list[Trade]) -> list[Trade]` — `sorted(rows, key=lambda t: (t.ts, t.symbol))`; `CleanError` | `clean_trades`, `CleanError` |

## 4. Workflow / pipeline

Serves the `daily` pipeline (contract §4), second step.

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 | `clean_trades(rows)` is called | log `rows_in` | — | — |
| 2 | — | `_dedupe`: `list(set(rows))` — exact duplicates collapse | unique rows, any order | none: `Trade` hashes by its fields |
| 3 | — | `_sort`: stable sort by `(ts, symbol)` | the table | none |
| 4 | — | log `rows_out`, `dropped = rows_in - rows_out`; return | `list[Trade]` | — |

The input list is never mutated; a new list is returned.

## 5. Interfaces

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `clean_trades` | `(rows: list[Trade]) -> list[Trade]` | `data/storage`, the `daily` pipeline | no | none; an empty list returns an empty list |
| `CleanError` | `class CleanError(ValueError)` | reserved for a row whose `ts` is naive after ingest — never expected today | no | — |

## 6. Error handling and logging

Logger `data.clean`. One `INFO` line at step 1 (`rows_in`) and one at step 4 (`rows_out`,
`dropped`), `extra=` keys only (repo contract, Shared conventions). No retries; nothing here
fails on well-formed input. `CleanError` exists so a naive timestamp — which ingest already
converts — has a named error if it ever appears.

## 7. Tests

Unit (`packages/data/tests/unit/clean/`): `_dedupe` on a list with two identical rows returns
one; `_sort` orders an out-of-order pair; `clean_trades` on an empty list returns `[]`; the
input list is unchanged after the call.

Intent (`packages/data/tests/intent/clean/`, the tester's): one file per §5 row plus a
workflow test that loads a small CSV with two exact duplicates and one out-of-order row
through `load_trades` and `clean_trades`.

Fixtures: six `Trade` rows built in `conftest.py`, two of them identical, one out of order;
an eight-row CSV written to `tmp_path` for the workflow test.

## 8. Pitfalls and risks

1. Sorting ties: two rows with the same `ts` and `symbol` but different `side` — the sort is
   stable, so file order decides; the contract asks for nothing finer.
2. Mutating the caller's list — `sorted()` returns a new list; never `rows.sort()`.
3. Dedupe of rows that differ only in float representation (`1.0` vs `1.00`) — equal in
   Python, so they collapse; that is what the brief means by exact duplicate.

## 9. Skills used

- `project-structure` — one module under the section path; no `configs.py` when there is no
  configuration.
- `python-style-guide` — docstrings, `from __future__ import annotations`, `extra=` logging.

## 10. Contract deviations

None.

## 11. Open questions

None.
