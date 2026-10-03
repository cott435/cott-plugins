# Package contract — `data`

## Purpose

Provides the **trades table**: the vendor's daily trades file loaded into one SQLite table,
one row per trade. Covers `load-trades` (section `ingest`: "read the vendor's trades file,
oldest trade first"), `store-trades` (section `store`: "insert the trades into the trades
table in one transaction") and `verify-trades` (section `ingest`: "check that every file in
the vendor's drop directory carries the header before any of them is loaded").

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read the vendor's trades CSV into trades, oldest first; check a vendor file's header | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `file:vendor-trades` |
| `store` | insert trades into the `trades` table | `packages/data/src/data/store/` | `docs/packages/data/design/store.md` | — | — | — |
| `surface` | the package's pipelines (§4), its commands and its public surface (§5) | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `store` | — |

## Section interfaces

- `ingest`: `read_trades(source: str) -> list[dict[str, str]]` — one dict per row of the CSV
  at `source`, with the keys `ts`, `symbol`, `price` and `size`, sorted by `ts`. Raises
  `csv.Error` when the file is not CSV, after copying it to `<source>.bad`.
  `check_header(path: str) -> bool` — whether the CSV file at `path` starts with the row
  `ts,symbol,price,size`; raises `csv.Error` when the file is not CSV, and copies nothing.
- `store`: `write_trades(target: str, trades: list[dict[str, str]]) -> int` — inserts one row
  per trade into the `trades` table of the SQLite database at `target`, in one transaction,
  and returns the number of rows inserted.

## Pipelines

- **load** — trigger: the `data-load` command. `ingest.read_trades` (trades, oldest first)
  → `store.write_trades` (rows in the `trades` table). Failure: `csv.Error` ends the run
  with the file copied to `<source>.bad` and nothing inserted.
- **verify** — trigger: the `data-verify` command. For every file in the drop directory, in
  name order: `ingest.check_header` (the file's header against the vendor's), re-read up to
  twice when the file is not yet CSV because the vendor is still writing it. Failure: a file
  without the header, or still not CSV after the re-reads, is a failure; the command exits 1
  when any file failed and writes nothing.

## Public surface (intent)

| name | section | consumer |
|---|---|---|
| `run_load` | `surface` | the `data-load` command; `backfill` (calls it once per file) |
| `run_verify` | `surface` | the `data-verify` command |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- A log event is named `data.<pipeline or section>.<event>`.
- `ingest` and `store` never import each other; `surface` imports each one's entry point
  from its module.

## Open decisions

- none
