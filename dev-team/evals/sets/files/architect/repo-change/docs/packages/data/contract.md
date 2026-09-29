# Package contract — `data`

Planned 2026-09-21 by `/dev-team:plan-package data` under `docs/architecture.md`.

## Purpose

`data` turns the analyst's CSV export into a clean, queryable SQLite copy and provides the
**Trades** shape (repo contract, Boundaries *data → analysis*) to `analysis`. Capabilities
covered (`covers`):

- **load trades** — `ingest`. Brief: "Read `data/trades.csv` (columns `ts`, `symbol`,
  `price`, `size`, `side`; `ts` is ISO 8601 UTC). The file is the only input: `source:
  dataset:trades`. Reject a row with a missing or unparseable field, and say which."
- **clean trades** — `clean`. Brief: "Drop exact duplicate rows and sort by `ts`. The export
  is known to contain duplicates and out-of-order rows."
- **store trades** — `storage`. Brief: "Persist the clean trades to a local SQLite file with
  the standard library's `sqlite3`; re-running on the same input must not duplicate rows."
- later — do not rule out: **second export format** ("A Parquet export of the same columns.")

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read the CSV export into `Trade` records; reject a row with a missing or unparseable field, naming the row and the field | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `dataset:trades` |
| `clean` | drop exact duplicate records and sort by `ts` | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `storage` | persist clean records to SQLite idempotently and read them back as **Trades** | `packages/data/src/data/storage/` | `docs/packages/data/design/storage.md` | — | `clean` | — |
| `surface` | the package's pipelines (§4) and public surface (§5) | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean`, `storage` | — |

## Section interfaces

- `ingest` — `Trade` (frozen dataclass, the **Trades** record: `ts`, `symbol`, `price`,
  `size`, `side`); `read_export(path: Path) -> list[Trade]`, raising
  `TradeParseError(row: int, field: str)` (a `DataError`) on the first bad row. `side`
  accepts exactly `buy` and `sell`; anything else is a bad row.
- `clean` — `dedupe(trades: list[Trade]) -> list[Trade]` drops records equal on all five
  fields, keeping the first; `sort_by_ts(trades: list[Trade]) -> list[Trade]` is a stable
  ascending sort; `clean_trades(trades: list[Trade]) -> list[Trade]` is
  `sort_by_ts(dedupe(trades))`.
- `storage` — `init_db(db_path: Path) -> None` creates table `trades` with a UNIQUE
  constraint over the five columns; `store_trades(trades: list[Trade], db_path: Path) -> int`
  inserts with `INSERT OR IGNORE` and returns the number of rows inserted;
  `load_trades(db_path: Path | None = None) -> list[Trade]` returns every stored row sorted
  by `ts`, `db_path` defaulting to `DATA_DB_PATH`.

## Pipelines

- **ingest** — trigger: `data-ingest <csv> [--db <path>]`. `ingest.read_export` →
  `list[Trade]` → `clean.clean_trades` → `list[Trade]` → `storage.store_trades` → `int`.
  Failure: a `TradeParseError` stops the run before anything is written; the message names
  the row and the field; exit code 1. Success prints `stored <n> new rows`.

## Public surface (intent)

| name | realized by | consumer |
|---|---|---|
| `Trade` | `ingest` | `analysis/features` |
| `load_trades` | `storage` | `analysis/features` |
| `DataError`, `TradeParseError` | `ingest` (`errors.py` at the package top level) | `data-ingest`, `analysis-summary` |
| `data-ingest` (CLI) | pipeline **ingest** | the analyst |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- The dedupe key is the whole record (repo contract: no id convention).
- Row numbers in error messages are 1-based and count the header line as row 1.

## Open decisions

- none
