# `data` — package contract

Written 2026-09-20 by /dev-team:plan-package data.

## Purpose

Ingests daily aggregate bars from polygon, cleans them into the repo shape `BarTable`, and
provides the `daily` pipeline the `features` package and the `data-daily` command run.
Provides: `BarTable`. Covers `daily-bars` — section `ingest` and `clean`; brief Notes: "one
vendor, daily bars only, adjusted prices".

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | fetches one symbol's daily aggregate bars from polygon for a date range and parses the payload into `Bar` rows | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `api:polygon` |
| `clean` | validates and de-duplicates `Bar` rows across symbols into a `BarTable` | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `surface` | the package's public surface: §4 Pipelines and §5 Public surface | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean` | — |

## Section interfaces

- `ingest` → `Bar` (frozen dataclass, one session of one symbol), `IngestError`,
  `parse_bars(payload, symbol) -> tuple[Bar, ...]`,
  `fetch_bars(symbol, start, end, *, client, retries=3) -> tuple[Bar, ...]`.
- `clean` → `clean_bars(bars: Iterable[Bar]) -> BarTable`.

## Pipelines

- `daily` — trigger: the `data-daily` command with `--run-date`. `ingest.fetch_bars` per symbol
  → `tuple[Bar, ...]` → `clean.clean_bars` → `BarTable` → parquet under `DATA_LANDING_DIR`.
  Failure: an `IngestError` for one symbol aborts the run; nothing is written.

## Public surface (intent)

| name | realized by | consumer |
|---|---|---|
| `BarTable` (shape) | `clean` | `features` |
| `daily_pipeline(run_date) -> Path` | `surface` | `data-daily` |

Nothing from `ingest` is public.

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Vendor payloads are never persisted by `ingest`; landing is `clean`'s and the pipeline's.

## Open decisions

- D1 — decided: timestamps tz-aware UTC.
- D2 — open: zero-volume bars.
