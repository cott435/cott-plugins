# Package contract — `data`

Written 2026-09-22 by `/dev-team:plan-package data`. Archived copy: `docs/history/2026-09-22-data-contract.md`.

## Purpose

Provides the **Trade** and **TradeTable** shapes of `docs/architecture.md`. Covers the
brief's `ingest` ("read the venue's CSV export as it comes"), `clean` ("drop the exact
duplicate rows the export repeats; order by time") and `store` ("keep it in one SQLite file
`analysis` can open") capabilities.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read the CSV into Trade rows | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `dataset:trades` |
| `clean` | remove exact duplicates, sort by time | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `storage` | persist and read back a TradeTable in SQLite | `packages/data/src/data/storage/` | `docs/packages/data/design/storage.md` | — | `ingest`, `clean` | — |
| `surface` | §4 Pipelines and §5 Public surface | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean`, `storage` | — |

## Section interfaces

| section | name | signature | returns to |
|---|---|---|---|
| `ingest` | `load_trades` | `(path: Path) -> list[Trade]` | `clean`, `storage`, `surface` |
| `ingest` | `Trade` | the **Trade** shape as a dataclass | everyone |
| `clean` | `clean_trades` | `(rows: list[Trade]) -> list[Trade]` — a TradeTable: no exact duplicates, sorted by `ts` then `symbol` | `storage`, `surface` |
| `storage` | `store_trades` | `(rows: list[Trade], db: Path) -> int` — rows inserted | `surface` |
| `storage` | `read_trades` | `(db: Path) -> list[Trade]` — a TradeTable | `surface`, `analysis` |
| `storage` | `store_clean` | `(csv: Path, db: Path) -> int` — `load_trades` → `clean_trades` → `store_trades` | `surface` |

## Pipelines

| pipeline | trigger | steps | crosses | failure | command |
|---|---|---|---|---|---|
| `daily` | the `data-daily` command | `ingest.load_trades` → `clean.clean_trades` → `storage.store_trades` | `list[Trade]` at every arrow | any `<Section>Error` stops the run; nothing partial is written | `data-daily --csv <path> --db <path>` |

## Public surface (intent)

| shape or name | realized by | consumer |
|---|---|---|
| **Trade** (`Trade`) | `ingest` | `analysis` |
| **TradeTable** (`read_trades`) | `storage` | `analysis` |
| `load_trades` | `ingest` | `analysis` (features, for a one-off backfill) |
| `daily` pipeline | `surface` | `data-daily` |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Standard library only (repo contract, Shared conventions). No `pandas`, no `attrs`.
- Every section logs one `INFO` line per step with `rows_in`, `rows_out`, `dropped`.

## Open decisions

- D1 — decided (UTC).
