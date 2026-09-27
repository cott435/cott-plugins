Mode: new

# Design — `data/storage`

Written 2026-09-24 by `dev-team:designer`. Run: `run-package data`.

## 1. Purpose and scope

Persists a **TradeTable** in one SQLite file and reads it back, and offers the one-call path
`store_clean` the `daily` pipeline runs. Owns the schema and the file; owns no parsing and no
cleaning.

## 2. Inputs and outputs

| direction | name | type | from / to |
|---|---|---|---|
| in | `rows` | `list[Trade]` — the return of `data/clean`'s `clean_trades` (contract §3; `packages/data/src/data/clean/README.md`, Entry points, as of 2026-09-24) | `data/clean` |
| in | `csv` | `Path` | the `data-daily` command, via the `daily` pipeline |
| in | `db` | `Path` — the SQLite file; created if absent | the command |
| out | rows inserted | `int` | the `daily` pipeline |
| out | the table | `list[Trade]` — a **TradeTable** | `analysis`, via the surface |

`Trade` is `data.ingest.Trade`.

## 3. Data model / internal contracts

One table, `trades`, `PRIMARY KEY (ts, symbol, price, size, side)`; `ts` stored as ISO 8601
UTC text. `INSERT OR IGNORE` makes a re-run idempotent.

**Module plan** — under `packages/data/src/data/storage/`:

| file | holds | defines (§5) |
|---|---|---|
| `__init__.py` | re-exports the four names | — |
| `schema.py` | `SCHEMA` (the `CREATE TABLE IF NOT EXISTS` statement); `_connect(db: Path) -> sqlite3.Connection` (creates the parent directory and the table) | — |
| `store.py` | `store_trades`, `read_trades`, `store_clean`, `StorageError` | all §5 rows |

No `configs.py`: paths are arguments.

## 4. Workflow / pipeline

Serves the `daily` pipeline (contract §4), third step; `store_clean` is the whole pipeline in
one call for the command.

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 | `store_clean(csv, db)` | `rows = load_trades(csv)` (`data/ingest`) | `list[Trade]` | `IngestError` propagates; nothing written |
| 2 | — | `table = clean_trades(rows)` (`data/clean`) — a `list[Trade]` | the TradeTable | `CleanError` propagates; nothing written |
| 3 | — | `store_trades(table, db)`: one transaction, `INSERT OR IGNORE` per row, commit | rows inserted | `sqlite3.Error` → `StorageError`; the transaction rolls back |
| 4 | `read_trades(db)` | `SELECT … ORDER BY ts, symbol` | `list[Trade]` | a missing file → `StorageError` |

## 5. Interfaces

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `store_trades` | `(rows: list[Trade], db: Path) -> int` | the `daily` pipeline | no | `StorageError` on any `sqlite3.Error` |
| `read_trades` | `(db: Path) -> list[Trade]` | `analysis`, via the surface | yes (contract §5, **TradeTable**) | `StorageError` when `db` does not exist |
| `store_clean` | `(csv: Path, db: Path) -> int` | the `data-daily` command, via the surface | no | the three errors above propagate |
| `StorageError` | `class StorageError(ValueError)` | callers of the three functions | no | — |

## 6. Error handling and logging

Logger `data.storage`. `INFO` at step 3 with `rows_in`, `rows_out` (inserted), `dropped`
(ignored duplicates); `extra=` keys only. No retries. A `sqlite3.Error` is wrapped in
`StorageError` with the file name, never the row.

## 7. Tests

Unit (`packages/data/tests/unit/storage/`): `_connect` creates the table; `store_trades` twice
with the same rows inserts on the first call only; `read_trades` on a missing file raises
`StorageError`; `ts` round-trips as an aware UTC datetime.

Intent (`packages/data/tests/intent/storage/`, the tester's): one file per §5 row plus a
workflow test running `store_clean` on an eight-row CSV with two exact duplicates.

Fixtures: six `Trade` rows in `conftest.py`; a `db` path under `tmp_path`; the CSV.

## 8. Pitfalls and risks

1. Storing `ts` as text loses nothing only if it is always UTC ISO 8601 — D1 guarantees it.
2. A partial write on error — one transaction per `store_trades` call.
3. `sqlite3` returns `str` for `ts`; `read_trades` must parse it back to an aware datetime.

## 9. Skills used

- `project-structure` — two modules under the section path; no `configs.py` without settings.
- `python-style-guide` — docstrings, `from __future__ import annotations`, `extra=` logging.

## 10. Contract deviations

None.

## 11. Open questions

None.
