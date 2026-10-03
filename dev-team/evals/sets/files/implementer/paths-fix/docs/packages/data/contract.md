# Package contract — `data`

Written 2026-09-22 by `/dev-team:plan-package data`. Archived copy: `docs/history/2026-09-22-data-contract.md`.

## Purpose

Provides the **Trade** and **TradeTable** shapes of `docs/architecture.md`. Covers the
brief's `ingest` ("read the venue's CSV export as it comes") and `clean` ("drop the exact
duplicate rows the export repeats; order by time") capabilities.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read the CSV into Trade rows | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `dataset:trades` |
| `clean` | remove exact duplicates, sort by time | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `surface` | §4 Pipelines and §5 Public surface | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean` | — |

## Section interfaces

| section | name | signature | returns to |
|---|---|---|---|
| `ingest` | `load_trades` | `(path: Path) -> list[Trade]` — rows in file order | `surface` |
| `ingest` | `Trade` | the **Trade** shape as a dataclass | everyone |
| `ingest` | `IngestError` | `class IngestError(ValueError)` | `surface` |
| `clean` | `clean_trades` | `(rows: list[Trade]) -> list[Trade]` — a TradeTable: no exact duplicates, sorted by `ts` then `symbol` | `surface` |

## Pipelines

| pipeline | trigger | steps | crosses | failure | command |
|---|---|---|---|---|---|
| `daily` | the `data-daily` command | `ingest.load_trades` → `clean.clean_trades` | `list[Trade]` at the arrow | any `<Section>Error` stops the run; the command exits 1 and writes nothing to stdout | `data-daily --csv <path>` |

## Public surface (intent)

| shape or name | realized by | consumer |
|---|---|---|
| **Trade** (`Trade`) | `ingest` | `analysis` |
| **TradeTable** (`daily`) | `surface` | `analysis` |
| `daily` pipeline | `surface` | `data-daily` |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Standard library only (repo contract, Shared conventions). No `pandas`, no `attrs`.
- Every section logs one `INFO` line per step with `rows_in`, `rows_out`, `dropped`, whichever
  that step has.

## Open decisions

- D1 — decided (UTC), scope `data/ingest`.
