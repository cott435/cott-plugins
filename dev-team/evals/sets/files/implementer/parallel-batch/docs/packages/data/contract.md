# Package contract — `data`

Written 2026-09-27 by `/dev-team:plan-package data`. Archived copy: `docs/history/2026-09-27-data-contract.md`.

## Purpose

Provides the **Trade** and **TradingDay** shapes of `docs/architecture.md`. Covers the
brief's `ingest` ("read the venue's export files as they come") and `calendar` ("which days
did the venue trade") capabilities.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | read an XVEN export into Trade rows | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | — |
| `calendar` | the venue's trading days | `packages/data/src/data/calendar/` | `docs/packages/data/design/calendar.md` | — | — | — |
| `surface` | §4 Pipelines and §5 Public surface | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `calendar` | — |

## Section interfaces

| section | name | signature | returns to |
|---|---|---|---|
| `ingest` | `load_export` | `(path: Path) -> list[Trade]` — rows in file order | `surface` |
| `ingest` | `Trade` | the **Trade** shape as a frozen dataclass | everyone |
| `ingest` | `IngestError` | `class IngestError(ValueError)` | `surface` |
| `calendar` | `trading_days` | `(start: date, end: date) -> list[date]` — both ends inclusive | `surface` |

## Pipelines

| pipeline | trigger | steps | crosses | failure | command |
|---|---|---|---|---|---|
| `daily` | the `data-daily` command | `calendar.trading_days` → `ingest.load_export` for each `data/raw/<date>.csv` of a trading day | `list[date]`, then `list[Trade]` | any `<Section>Error` stops the run; nothing partial is returned | `data-daily --raw data/raw --since <date>` |

## Public surface (intent)

| shape or name | realized by | consumer |
|---|---|---|
| **Trade** (`Trade`) | `ingest` | `analysis` |
| **TradingDay** (`trading_days`) | `calendar` | `analysis` |
| `daily` pipeline | `surface` | `data-daily` |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Standard library only, except `python-dateutil` in `ingest` (D2).
- Every section logs one `INFO` line per step with the counts that step has.

## Open decisions

- D1 — decided (UTC). D2 — decided (`python-dateutil`). D3 — open, repo-wide.
