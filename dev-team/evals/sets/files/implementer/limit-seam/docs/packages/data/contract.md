# Package contract — `data`

Written 2026-09-22 by `/dev-team:plan-package data`. Archived copy: `docs/history/2026-09-22-data-contract.md`.

## Purpose

Provides the **Trade** and **Bar** shapes of `docs/architecture.md`. Covers the brief's
`ingest` ("read the venue's CSV export as it comes") and `bars` ("five-minute bars, or any
other width, for the symbol I ask for, over the hours I ask for") capabilities.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read the CSV into Trade rows | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `dataset:trades` |
| `bars` | build one symbol's fixed-width bars over a time window from Trade rows | `packages/data/src/data/bars/` | `docs/packages/data/design/bars.md` | — | `ingest` | — |
| `surface` | §4 Pipelines and §5 Public surface | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `bars` | — |

## Section interfaces

| section | name | signature | returns to |
|---|---|---|---|
| `ingest` | `load_trades` | `(path: Path) -> list[Trade]` | `surface` |
| `ingest` | `Trade` | the **Trade** shape as a dataclass | everyone |
| `bars` | `build_bars` | seven inputs — `rows`, `symbol`, `start`, `end`, `interval`, `min_size`, `fill_gaps` — `-> list[Bar]`, in time order | `surface`, `analysis` |
| `bars` | `Bar` | the **Bar** shape as a frozen dataclass | everyone |
| `bars` | `BarsError` | `class BarsError(ValueError)` | `surface` |

## Pipelines

| pipeline | trigger | steps | crosses | failure | command |
|---|---|---|---|---|---|
| `daily` | the `data-daily` command | `ingest.load_trades` → `bars.build_bars` | `list[Trade]`, then `list[Bar]` | any `<Section>Error` stops the run; nothing partial is printed | `data-daily --csv <path> --symbol <symbol> --from <ts> --to <ts> --interval <minutes>` |

## Public surface (intent)

| shape or name | realized by | consumer |
|---|---|---|
| **Trade** (`Trade`) | `ingest` | `analysis` |
| **Bar** (`Bar`) | `bars` | `analysis` |
| `build_bars` | `bars` | `analysis` (features, at widths the pipeline does not run) |
| `daily` pipeline | `surface` | `data-daily` |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Standard library only (repo contract, Shared conventions). No `pandas`, no `attrs`.
- Every section logs one `INFO` line per step with the counts that step has.

## Open decisions

- D1 — decided (UTC), scope `data/ingest`.
