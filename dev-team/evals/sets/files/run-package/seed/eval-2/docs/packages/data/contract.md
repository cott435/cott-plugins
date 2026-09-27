# `data` — package contract

Written: 2026-09-26 by `/dev-team:plan-package data`, under `docs/architecture.md` (2026-09-26).
Package path: `packages/data`. Seeded for the `run-package` eval set (eval 2: the `ingest`
row claims a `venue` column that `docs/sources/trades.md` and `docs/architecture.md` do not).

## Purpose

Load the analyst's CSV export of trades, reject malformed rows by row and field, drop exact
duplicates, sort by time, and persist the result to a local SQLite file that a second run on
the same input leaves unchanged. Covers the brief's `load trades`, `clean trades` and
`store trades`.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | `load trades`: read `data/trades.csv` into `Trade` records in file order, carrying the export's `venue` column; reject a row with a missing or unparseable field and say which row and which field | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | `csv`, `datetime` (stdlib) | — | `dataset:trades` |
| `clean` | `clean trades`: drop exact duplicate rows and sort by `ts` | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | stdlib | `ingest` | — |
| `storage` | `store trades`: persist clean trades to SQLite through `sqlite3`; a re-run on the same input inserts nothing | `packages/data/src/data/storage/` | `docs/packages/data/design/storage.md` | `sqlite3` (stdlib) | `clean` | — |
| `surface` | §4 Pipelines and §5 Public surface: the package's top-level re-exports, the `data-ingest` command, `docs/packages/data/interface.md` | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean`, `storage` | — |

## Section interfaces

Signatures are this package's; shapes are `docs/architecture.md` **Boundaries**.

### ingest

- `Trade` — the repo shape `Trade`, a frozen dataclass: `ts: datetime` (tz-aware UTC),
  `symbol: str`, `price: float`, `size: int`, `side: Literal["buy", "sell"]`, `venue: str`
  (the export's `venue` column, a venue code such as `XNAS`; required, never empty).
- `read_trades(path: Path) -> list[Trade]` — every data row of the CSV, in file order,
  duplicates included.
- `IngestError(DataError)` — raised on the first rejected row, with `row: int` (1-based data
  row), `field: str` and `reason: str`; its message names all three.
- `DataError(Exception)` — the package base exception, defined here, re-raised nowhere else.

### clean

- `clean_trades(trades: list[Trade]) -> list[Trade]` — exact duplicates (all five fields
  equal) removed, then a stable sort by `ts`.

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
| `data.Trade` | shape, including `venue` | `analysis/features`, `analysis/report` |
| `data.load_trades` | function; yields `Trade` records with their `venue` | `analysis/features` |
| `data.ingest_pipeline` | pipeline | the analyst, through `data-ingest` |
| `data.DataError` | exception | `analysis` |

## Consumes

No upstream package. External: `dataset:trades` at `data/trades.csv`; probe
`docs/sources/trades.md`, which serves `data/ingest`.

## Package conventions

- Configuration: `DATA_CSV` (default `data/trades.csv`), `DATA_DB` (default `trades.sqlite`),
  read in `configs.py` with `os.environ`.
- Logging: logger `data`.
- The intent suite lives at `tests/intent/<section>/` (the tester's); unit tests beside the
  package as `project-structure` places them.

## Open decisions

None.
