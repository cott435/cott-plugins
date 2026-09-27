# `data/ingest`

## Purpose

Pulls one symbol's daily bars from the vendor over `VENDOR_KEY` and returns them as a
BarFrame exactly as the vendor sent them.

## Files

| file | responsibility | used by |
|---|---|---|
| `client.py` | `fetch_bars`, the retry loop, the vendor row → BarFrame mapping | the `daily` pipeline |
| `errors.py` | `VendorUnavailable` | `client.py`, the `daily` pipeline |

## Entry points and interfaces

| name | signature | use | Public |
|---|---|---|---|
| `fetch_bars` | `(symbol: str, start: date, end: date) -> DataFrame` | one symbol's bars for the range | yes |

The frame's columns are `symbol` (str), `timestamp` (datetime64[ns], naive UTC midnight),
`open`, `high`, `low`, `close` (float64), `volume` (int64). Rows come back in vendor order,
not sorted.

## Pipeline / workflow

`_get` (HTTP, up to four attempts) → `_to_frame` → the caller. Part of the `daily` pipeline.

## Configuration

| env var | default | what it controls |
|---|---|---|
| `VENDOR_KEY` | — | the vendor API key |
| `DATA_RETRIES` | `3` | retries on a 429 |

## Running and testing

`uv run pytest packages/data/tests/unit/ingest -q`

## Implementation notes

- Retries only on 429; any other non-2xx raises immediately.
- During the vendor's end-of-day correction window (about 21:00–22:00 UTC) a response can
  hold the same `timestamp` twice: the first row is the preliminary bar, the later row is the
  corrected one and carries the corrected `volume`. `fetch_bars` passes both through; it is
  the consumer's job to resolve them.
- `volume` is 0 on a day the exchange was open but the symbol did not trade; the vendor
  never omits such a day.
