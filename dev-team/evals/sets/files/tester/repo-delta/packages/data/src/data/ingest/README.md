# `data/ingest`

## Purpose

Fetches one symbol's daily aggregate bars from polygon for a date range and parses the payload
into `Bar` rows. Nothing here persists or de-duplicates; that is `clean`.

## Files

| file | holds |
|---|---|
| `models.py` | `Bar`, `IngestError` |
| `parse.py` | `parse_bars` |
| `fetch.py` | `VendorClient`, `VendorError`, `fetch_bars` |
| `configs.py` | `IngestSettings` |

## Entry points and interfaces

| name | signature | Public |
|---|---|---|
| `Bar` | frozen dataclass `symbol, ts, open, high, low, close, volume` | no |
| `IngestError` | `IngestError(reason: str, symbol: str)` | no |
| `VendorClient` | `Protocol`: `get(path, params) -> dict` | no |
| `parse_bars` | `(payload: dict[str, Any], symbol: str) -> tuple[Bar, ...]` | no |
| `fetch_bars` | `(symbol, start, end, *, client, retries=3) -> tuple[Bar, ...]` | no |

## Pipeline / workflow

Build the path and params (`adjusted`, `sort`, `limit=50000`) → `client.get` with 429 retried `retries` times → `parse_bars` → one INFO
record `event=data.ingest.fetch symbol=… bars=…`.

## Configuration

`DATA_VENDOR_KEY` via `IngestSettings.vendor_key`; `retries` default 3.

## Running and testing

`PYTHONPATH=src python -m pytest tests/unit/ingest tests/intent/ingest -q` from `packages/data`.

## Implementation notes

- Deviation `data/ingest — 2026-09-24 — deviation — 1`: a payload with no `results` key
  returns `()` with a WARNING instead of raising (see `docs/packages/data/deviations/ingest.md`).
- Change `page-limit`: every request sends `limit=50000`.
