# Package contract — `data`

## Purpose

Provides the **trades table**: the vendor's daily trades file loaded into one SQLite table,
one row per trade. Covers `load-trades` (section `ingest`: "read the vendor's trades file,
oldest trade first") and `store-trades` (section `store`: "insert the trades into the trades
table in one transaction").

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read the vendor's trades CSV into trades, oldest first | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `file:vendor-trades` |
| `store` | insert trades into the `trades` table | `packages/data/src/data/store/` | `docs/packages/data/design/store.md` | — | — | — |
| `surface` | the package's pipelines (§4), its command and its public surface (§6) | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `store` | — |

## Section interfaces

- `ingest`: `read_trades(source: str) -> list[dict[str, str]]` — one dict per row of the CSV
  at `source`, with the keys `ts`, `symbol`, `price` and `size`, sorted by `ts`. Raises
  `csv.Error` when the file is not CSV, after copying it to `<source>.bad`.
- `store`: `write_trades(target: str, trades: list[dict[str, str]]) -> int` — inserts one row
  per trade into the `trades` table of the SQLite database at `target`, in one transaction,
  and returns the number of rows inserted.

## Pipelines

- **load** — trigger: the `data-load` command. `ingest.read_trades` (trades, oldest first)
  → `store.write_trades` (rows in the `trades` table). Failure: `csv.Error` ends the run
  with the file copied to `<source>.bad` and nothing inserted.

## Call paths

- `data-load` (budget 1):
  - file read: 1 `cli.load` → 2 `pipelines.run_load` → 3 `ingest.read_trades` → `open`

## Public surface (intent)

| name | section | consumer |
|---|---|---|
| `run_load` | `surface` | the `data-load` command; `backfill` (calls it once per file) |

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
