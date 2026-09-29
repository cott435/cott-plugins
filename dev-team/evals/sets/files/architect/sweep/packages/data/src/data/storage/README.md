# `data/storage`

## Purpose

Persists clean records to SQLite idempotently and reads them back as **Trades**.

## Files

| File | What it holds |
|---|---|
| `db.py` | `init_db`, `store_trades`, `load_trades`, `_db_path` |

## Entry points and interfaces

| Name | Signature | Public |
|---|---|---|
| `init_db` | `(db_path: Path) -> None` | no |
| `store_trades` | `(trades: list[Trade], db_path: Path) -> int` | no |
| `load_trades` | `(db_path: Path \| None = None) -> list[Trade]` | yes — contract §5, consumer `analysis/features` |

## Pipeline / workflow

`store_trades`: `init_db` → `INSERT OR IGNORE` → count inserted. `load_trades`: `SELECT …
ORDER BY ts` → `list[Trade]`.

## Configuration

`DATA_DB_PATH` (default `./trades.sqlite`), read only when `load_trades` gets no path.

## Running and testing

`uv run pytest packages/data/tests/intent/storage`

## Implementation notes

Idempotence is the UNIQUE constraint over all five columns (contract §3). No deviations
recorded for this section.
