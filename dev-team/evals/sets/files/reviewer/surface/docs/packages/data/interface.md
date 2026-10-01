# Interface — `data`

Daily bars from the vendor, cleaned into one row per symbol and business day. Other packages
import the names below from `data`, never from a section's module.

## Public names

| name | kind | signature | providing module | consumer | since |
|---|---|---|---|---|---|
| `data.fetch_bars` | function | `(symbol: str, start: date, end: date) -> DataFrame` | `data.ingest.client` | the `daily` pipeline | 2026-09-27 |
| `data.clean_bars` | function | `(df: DataFrame) -> DataFrame` | `data.clean.api` | the `daily` pipeline; `features` (re-cleans a cached frame) | 2026-09-27 |

`import data` loads neither section: each name is imported on first access. The contract's
third row, `BarFrame`, is a shape and is under **Shapes provided**.

## Pipelines

- **daily** — `data.pipelines.daily`: per symbol, `fetch_bars` → `clean_bars` → one parquet
  file `DATA_LANDING_DIR/<run_date>/<symbol>.parquet`, where `<run_date>` is the run's end
  date. A symbol with no bars is skipped and logged as `data.daily.skipped`;
  `VendorUnavailable` ends the run. D3 is open: one parquet file per symbol is the
  assumption, marked `TODO(decision D3)` at `packages/data/src/data/pipelines.py:56`. `daily`
  and `main` take a `fetch` argument so tests replace the vendor without a network.

## CLI commands

| command | entry point | arguments | what it runs |
|---|---|---|---|
| `data-daily` | `data.pipelines:main` | `SYMBOL [SYMBOL ...] --start YYYY-MM-DD --end YYYY-MM-DD` | the `daily` pipeline; exits 0 when the run finished, 2 when the vendor was unavailable |

## Configuration

| env var | default | what it controls |
|---|---|---|
| `DATA_LANDING_DIR` | — | where the run's folder is created |
| `VENDOR_KEY` | — | the vendor API key (`ingest`) |
| `DATA_RETRIES` | `3` | retries on a 429 (`ingest`) |

## Shapes provided

- **BarFrame** — a `pandas.DataFrame` with the columns `symbol` (str), `timestamp`
  (datetime64[ns], naive UTC midnight), `open`, `high`, `low`, `close` (float64), `volume`
  (int64), in that order: the column set `REQUIRED` in `packages/data/src/data/clean/api.py`
  and `COLUMNS` in `packages/data/src/data/ingest/client.py`. `clean_bars` returns one row
  per symbol and business day, sorted by `symbol, timestamp`.

## Deviations

None.

## Consumers (computed)

Snapshot, 2026-09-27: `features`.
