# `data/ingest`

## Purpose

Pulls daily bars from the vendor API and lands them as parquet.

## Files

| File | What it holds |
|---|---|
| `loader.py` | `load_bars`, the vendor call and the retry loop |

## Entry points and interfaces

| Name | Signature | Public |
|---|---|---|
| `load_bars` | `(symbol: str, start: date, end: date) -> DataFrame` | yes |

## Pipeline / workflow

`load_bars` → parquet under `DATA_LANDING_DIR/<run_date>/`.

## Configuration

| Variable | Default | Meaning |
|---|---|---|
| `DATA_VENDOR_KEY` | — (required) | vendor API key |
| `DATA_LANDING_DIR` | `./landing` | where landed parquet goes |
| `DATA_RETRIES` | `3` | vendor calls retried on 429 and 503 |

## Running and testing

`uv run pytest packages/data/tests/test_ingest.py`

## Implementation notes

Retries only on 429 and 503; anything else raises immediately.
