Mode: new

# Design — `data/clean`

Written 2026-10-01 by `dev-team:designer`. Run: `run-package data`.

## 1. Purpose and scope

Turns the rows `ingest` reads into a **TradeTable**: exact duplicate rows collapse to one, the
result is sorted by `ts` then `symbol`. Owns nothing else — no parsing, no persistence, no
validation beyond what the row type already guarantees.

## 2. Inputs and outputs

| direction | name | type | from / to |
|---|---|---|---|
| in | `rows` | `list[Trade]` | `data/ingest` — `load_trades` (`packages/data/src/data/ingest/README.md`, Entry points) |
| out | the table | `list[Trade]` — a **TradeTable** (`docs/architecture.md`, Boundaries) | `data/storage`, the `daily` pipeline |

`Trade` is `data.ingest.Trade`, mutable and unhashable (its README); this section defines no
row type of its own.

Upstream packages: none

## 3. Data model / internal contracts

No state, no tables, no settings (`configs.py` is not needed; the section has no
configuration).

**Module plan** — under `packages/data/src/data/clean/`:

| file | holds | defines (§5) |
|---|---|---|
| `__init__.py` | re-exports `clean_trades`, `CleanError` | — |
| `rules.py` | `clean_trades`; `_key(t: Trade, fields: tuple[str, ...] = ("ts", "symbol", "price", "size", "side")) -> tuple` — the values of `fields`, in order; `_dedupe(rows: list[Trade]) -> list[Trade]` — walks `rows` in order and keeps the **first** row of each `_key`, so the survivors stay in file order; `_sort(rows: list[Trade]) -> list[Trade]` — `sorted(rows, key=lambda t: (t.ts, t.symbol))`; `CleanError` | `clean_trades`, `CleanError` |

`_key` and `_dedupe` are generic over which fields make two rows the same trade; the section
names the fields in one place, the default of `fields`.

## 4. Workflow / pipeline

Serves the `daily` pipeline (contract §4), second step.

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 | `clean_trades(rows)` is called | log `rows_in` | — | — |
| 2 | — | `_dedupe`: one pass in input order, a `set` of keys seen; the first row of each key is kept | unique rows, in input order | none |
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
fails on well-formed input, and `CleanError` is the only exception type the section defines.

## 7. Tests

Unit (`packages/data/tests/unit/clean/`): `_dedupe` on a list with two identical rows returns
one; `_dedupe` on the `side_pair` fixture returns both rows; `_sort` orders an out-of-order
pair; `clean_trades` on an empty list returns `[]`; the input list is unchanged after the
call.

Fixtures (`packages/data/tests/unit/clean/conftest.py`): `side_pair` — two `Trade` rows equal
in `ts`, `symbol`, `price` and `size`, one a `buy` and one a `sell`.

Intent (`packages/data/tests/intent/clean/`, the tester's): one file per §5 row plus a
workflow test that loads a small CSV with two exact duplicates and one out-of-order row
through `load_trades` and `clean_trades`.

## 8. Pitfalls and risks

1. Sorting ties: two rows with the same `ts` and `symbol` but a different `side` or `price`
   — the sort is stable, so **file order decides**, and `_dedupe` must hand `_sort` the rows
   in file order for that to hold. The contract asks for nothing finer.
2. Mutating the caller's list — `sorted()` returns a new list; never `rows.sort()`.
3. `Trade` is unhashable — `set(rows)` raises `TypeError`; dedupe by `_key`.

## 9. Skills used

- `project-structure` — one module under the section path; no `configs.py` when there is no
  configuration.
- `python-style-guide` — docstrings, `from __future__ import annotations`, `extra=` logging.

## 10. Contract deviations

None.

## 11. Open questions

- OQ-data-clean-1 — whether `side` counts toward an exact duplicate — is D2, open; its
  assumption is what §3 builds.
- D2 binds this section: §3 the default of `_key`'s `fields`.
- D3 binds data/storage, not this one
