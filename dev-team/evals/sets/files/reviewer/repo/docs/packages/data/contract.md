# Package contract — `data`

## Purpose

Provides the **BarFrame** shape: daily bars pulled from the vendor and cleaned into one row
per symbol and business day. Covers `daily-bars` (section `ingest`: "pull every symbol's
daily bars from the vendor, retrying its rate limit") and `clean-bars` (section `clean`:
"one bar per symbol per trading day, no duplicates, no zero-volume days, gaps filled").

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| `ingest` | fetch daily bars from the vendor as a BarFrame | `packages/data/src/data/ingest/` | `docs/packages/data/design/ingest.md` | — | — | `api:vendor` |
| `clean` | resolve duplicates, drop zero-volume rows, fill gaps to one row per symbol and business day | `packages/data/src/data/clean/` | `docs/packages/data/design/clean.md` | — | `ingest` | — |
| `surface` | the package's pipelines (§4) and public surface (§5) | `packages/data/src/data/` | `docs/packages/data/design/surface.md` | — | `ingest`, `clean` | — |

## Section interfaces

- `ingest`: `fetch_bars(symbol: str, start: date, end: date) -> DataFrame` — a BarFrame for
  one symbol, as the vendor returned it (duplicates and zero-volume rows included).
  Raises `VendorUnavailable` after three retries on a 429.
- `clean`: `clean_bars(df: DataFrame) -> DataFrame` — the BarFrame `ingest.fetch_bars`
  returns, with the same columns, one row per `(symbol, timestamp)`, one row per business
  day between the first and last bar of each symbol. Raises `MissingColumns` when a
  BarFrame column is absent and `EmptyBars` when `df` has no rows.

## Pipelines

- **daily** — trigger: the `data-daily` command. `ingest.fetch_bars` (BarFrame per symbol)
  → `clean.clean_bars` (BarFrame) → parquet under `DATA_LANDING_DIR/<run_date>/`. Failure:
  `VendorUnavailable` aborts the run with exit 2; `EmptyBars` skips the symbol and logs
  `data.daily.skipped`.

## Public surface (intent)

| name | section | consumer |
|---|---|---|
| `fetch_bars` | `ingest` | the `daily` pipeline |
| `clean_bars` | `clean` | the `daily` pipeline; `features` (re-cleans a cached frame) |
| `BarFrame` (shape) | `clean` | `features` |

## Consumes

| upstream package | name | shape | status |
|---|---|---|---|
| — | — | — | — |

## Package conventions

- Log events are `data.<section>.<event>`; fields go in `extra`, never in the message.
- Sections never import each other's modules; a section consumes a sibling only through the
  names its README marks `Public: yes`.

## Open decisions

- D1 — decided: duplicates are the same `(symbol, timestamp)`.
- D2 — open: no flag column on filled bars (assumption).
