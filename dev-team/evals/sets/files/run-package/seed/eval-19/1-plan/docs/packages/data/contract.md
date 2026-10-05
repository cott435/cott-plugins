# `data` — package contract

Written: 2026-09-26 by `/dev-team:plan-package data`, under `docs/architecture.md` (2026-09-26).
Package path: `packages/data`. Seeded for the `run-package` eval set (eval 19: the common
package planned under 2.7, so the `clean` row is marked as a data stage — `stage:rawtrades` in
its `source` cell, `dev-team:data-quality` in `builds with`, and the stage's line under
**Package conventions**).

## Purpose

Load the analyst's CSV export of trades, reject malformed rows by row and field, set aside
every row that is not a trade the analyst can use (exact duplicates among them) with the reason
it was set aside, sort what is left by time, and persist the result to a local SQLite file
that a second run on the same input leaves unchanged. Covers the brief's `load trades`,
`clean trades` and `store trades`.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | `load trades`: read `data/trades.csv` into `Trade` records in file order; reject a row with a missing or unparseable field and say which row and which field | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | `csv`, `datetime` (stdlib) | — | `dataset:trades` |
| `clean` | `clean trades`: sort the rows `ingest` read into the ones to keep, ordered by `ts`, and the ones set aside, each with its reason; no row is lost and none is changed without a record | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | `dev-team:data-quality` | `ingest` | `stage:rawtrades` |
| `storage` | `store trades`: persist clean trades to SQLite through `sqlite3`; a re-run on the same input inserts nothing | `packages/data/src/data/storage/` | `docs/packages/data/design/storage.md` | `sqlite3` (stdlib) | `clean` | — |
| `surface` | §4 Pipelines and §5 Public surface: the package's top-level re-exports, the `data-ingest` command, `docs/packages/data/interface.md` | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean`, `storage` | — |

## Section interfaces

Signatures are this package's; shapes are `docs/architecture.md` **Boundaries**.

### ingest

- `Trade` — the repo shape `Trade`, a frozen dataclass: `ts: datetime` (tz-aware UTC),
  `symbol: str`, `price: float`, `size: int`, `side: Literal["buy", "sell"]`.
- `read_trades(path: Path) -> list[Trade]` — every data row of the CSV, in file order,
  duplicates included.
- `IngestError(DataError)` — raised on the first rejected row, with `row: int` (1-based data
  row), `field: str` and `reason: str`; its message names all three.
- `DataError(Exception)` — the package base exception, defined here, re-raised nowhere else.

### clean

- `Rejected` — a frozen dataclass: `trade: Trade` (the row as `ingest` read it) and
  `reason: str` (why it was set aside or altered).
- `clean_trades(trades: list[Trade], rejects: Path | None = None) -> list[Trade]` — the rows
  to keep, in a stable sort by `ts`. Every row it does not keep as read is appended to the
  rejects file, one CSV line per row: the five `Trade` fields, then `reason`. `rejects`
  defaults to the configured `DATA_REJECTS`; the file is created with its header when absent.
  Which rows are set aside, and how each is treated, is the design's, from the profile of the
  stage (`docs/sources/rawtrades.md`) and the decisions it raised.

### storage

- `store_trades(trades: list[Trade], db: Path) -> int` — creates the `trades` table if absent,
  inserts the rows not already present, returns the number inserted (`0` on a re-run of the
  same input).
- `load_trades(db: Path) -> list[Trade]` — every stored row, ordered by `ts`.

## Pipelines

- `ingest_pipeline(csv_path: Path, db: Path) -> int` — `read_trades` → `clean_trades` →
  `store_trades`; returns the rows inserted. Run by the `data-ingest` command:
  `data-ingest [--csv PATH] [--db PATH]`, defaults from configuration.

## Public surface (intent)

| name | kind | consumer |
|---|---|---|
| `data.Trade` | shape | `analysis/features`, `analysis/report` |
| `data.load_trades` | function | `analysis/features` |
| `data.ingest_pipeline` | pipeline | the analyst, through `data-ingest` |
| `data.DataError` | exception | `analysis` |

## Consumes

No upstream package. External: `dataset:trades` at `data/trades.csv`; probe
`docs/sources/trades.md`, which serves `data/ingest`.

## Package conventions

- Configuration: `DATA_CSV` (default `data/trades.csv`), `DATA_DB` (default `trades.sqlite`),
  `DATA_REJECTS` (default `rejects/trades.csv`: `clean`'s store, the rows it set aside), read
  in `configs.py` with `os.environ`.
- `stage:rawtrades` — the trade rows ingest reads; lands at data/trades.csv; pull cap 500 rows, D1
- Logging: logger `data`.
- The intent suite lives at `tests/intent/<section>/` (the tester's); unit tests beside the
  package as `project-structure` places them.

## Open decisions

None. D1 (the pull cap of `stage:rawtrades`) is decided in `docs/decisions.md`.
