# `data` — interface

The public surface of `data` as shipped. 2026-09-12.

## Public names

| Name | Kind | Signature | Providing module | Consumer | Since |
|---|---|---|---|---|---|
| `load_bars` | function | `(symbol: str, start: date, end: date) -> DataFrame` | `data.ingest.loader` | `features` | 2026-09-12 |
| `clean_bars` | function | `(df: DataFrame) -> DataFrame` | `data.clean.rules` | `features` | 2026-09-12 |

## Pipelines

`daily_pipeline(run_date: date) -> Path` — ingest, clean, write parquet. On a vendor 429 it
retries three times and then raises `VendorUnavailable`. Run by the `data-daily` command.

## CLI commands

| Command | Entry point | Arguments | What it runs |
|---|---|---|---|
| `data-daily` | `data.cli:daily` | `--run-date` (date, default today, "the session to pull"); `--symbols` (str, default `SP500`, "symbol list name") | `daily_pipeline` for one run date |

## Configuration

Env prefix `DATA_`. `DATA_VENDOR_KEY` (no default, required), `DATA_LANDING_DIR` (default
`./landing`), `DATA_RETRIES` (default `3`).

## Shapes provided

| Repo-contract shape | Realized by | Defined in |
|---|---|---|
| `bars` | `DataFrame[ts, symbol, open, high, low, close, volume]` | `data.clean.rules.BAR_COLUMNS` |

## Deviations

| Document | Said | Shipped |
|---|---|---|
| `surface.md` | `load_bars` takes a `symbols` list | takes one `symbol`; the list form is `daily_pipeline`'s |

## Consumers (computed)

Snapshot 2026-09-12: `packages/features` (imports `data`), `docs/packages/features/contract.md`
**Consumes** names `data`.
