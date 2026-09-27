Mode: new

# Design — `data/ingest`

Designed 2026-09-23 from `docs/packages/data/contract.md` (row `ingest`), `docs/architecture.md`
and `docs/sources/polygon.md` (§data/ingest).

1. **Purpose and scope**

Owns fetching one symbol's daily aggregate bars from polygon for a date range and parsing the
payload into `Bar` rows. Does not validate across symbols, de-duplicate, or write anything to
disk — that is `clean` and the `daily` pipeline.

2. **Inputs and outputs**

- In: `symbol: str`, `start: date`, `end: date`, a `VendorClient` (§5). The vendor payload is
  the shape under `docs/sources/polygon.md` §3: `results: list[{t: int (epoch ms), o, h, l,
  c: float, v: int}]`, `resultsCount: int`, `status: str`; `results` is absent when
  `resultsCount` is 0 (§8 Quirks). `vw` and `n` are ignored.
- Out: `tuple[Bar, ...]` sorted ascending by `ts`; each `Bar` is one row of the repo shape
  `BarTable` (`docs/architecture.md` Boundaries).
- Configuration: `DATA_VENDOR_KEY` (`docs/architecture.md` Shared conventions), read by
  `configs.py`; the client, not this section, sends it.

3. **Data model / internal contracts**

- `Bar` — frozen dataclass; fields in this order: `symbol: str`, `ts: datetime` (tz-aware
  UTC, D1), `open: float`, `high: float`, `low: float`, `close: float`, `volume: int`.
- `IngestError(Exception)` — attributes `reason: str`, `symbol: str`; `str()` is
  `f"{reason}: {symbol}"` per the repo error convention.
- `VendorError(Exception)` — attribute `status: int`; what a `VendorClient` raises on any
  non-2xx response.

**Module plan** (under `packages/data/src/data/ingest/`):

| module | defines | §5 interfaces |
|---|---|---|
| `models.py` | `Bar`, `IngestError` | `Bar`, `IngestError` |
| `parse.py` | `parse_bars`, the epoch-ms → UTC conversion | `parse_bars` |
| `configs.py` | `IngestSettings` (`vendor_key` from `DATA_VENDOR_KEY`, `retries: int = 3`, `base_url`) per `project-structure` §3 | — |
| `__init__.py` | docstring only | — |

4. **Workflow / pipeline** (serves the package pipeline `daily`)

1. Build the request: path `/v2/aggs/ticker/{symbol}/range/1/day/{start}/{end}` with ISO
   dates, params `{"adjusted": "true", "sort": "asc"}`. Trigger: `fetch_bars` called.
   Output: path and params. Failure: `end < start` raises `IngestError("empty range")` before
   any call.
2. `client.get(path, params)`. Output: the payload dict. Failure: a `VendorError` with
   `status == 429` is retried up to `retries` times (at most `retries + 1` calls); a 429 still
   failing, or any other `status >= 400`, raises `IngestError(f"vendor {status}")`.
3. `parse_bars(payload, symbol)`. Output: `tuple[Bar, ...]` ascending by `ts`. Failure: §6.
4. Log one INFO record `event=data.ingest.fetch symbol=<symbol> bars=<n>` and return.

5. **Interfaces**

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `Bar` | frozen dataclass, fields in §3 order | `clean` | no | — |
| `IngestError` | `IngestError(reason: str, symbol: str)` | `clean`; the `daily` pipeline | no | — |
| `VendorClient` | `Protocol`: `get(self, path: str, params: dict[str, str]) -> dict[str, Any]`; raises `VendorError(status)` on any non-2xx | `fetch_bars`; the real client is the `surface` section's | no | `VendorError` |
| `parse_bars` | `(payload: dict[str, Any], symbol: str) -> tuple[Bar, ...]` | `fetch_bars`; `clean` (re-parse of landed payloads) | no | `IngestError` `"missing results"`, `"negative volume"` |
| `fetch_bars` | `(symbol: str, start: date, end: date, *, client: VendorClient, retries: int = 3) -> tuple[Bar, ...]` | `clean`; the `daily` pipeline | no | `IngestError` `"empty range"`, `"vendor <status>"` |

6. **Error handling and logging**

- A payload with no `results` key → `IngestError(reason="missing results", symbol=symbol)`.
- Any row with `v < 0` → `IngestError(reason="negative volume", symbol=symbol)`; no partial
  result is returned.
- `end < start` → `IngestError(reason="empty range", symbol=symbol)`, and the client is never
  called.
- `VendorError` with `status == 429` → retried up to `retries` times; still failing, or any
  other `status >= 400` → `IngestError(reason=f"vendor {status}", symbol=symbol)`.
- Each successful `fetch_bars` logs exactly one record at INFO on the logger `data.ingest`,
  message `event=data.ingest.fetch symbol=<symbol> bars=<n>`. Nothing else is logged at INFO
  or above on the happy path.
- Rows with `v == 0` are kept, unchanged (D2 assumption).

7. **Tests**

Fixture: `docs/sources/polygon.sample.json` (three `AAPL` sessions, 2024-03-04 to
2024-03-06), copied to `tests/fixtures/polygon.sample.json`. A fake `VendorClient` built to
§5: a queue of responses, each a payload dict or a `VendorError`; records every `(path,
params)` it was called with.

- `parse_bars` on the sample → three `Bar` rows, `ts` ascending, every `ts` tz-aware UTC (D1);
  the first is `2024-03-04T05:00:00+00:00` with `open == 176.15`, `volume == 81510101`.
- `parse_bars` on the sample with `results` reversed → the same three rows, still ascending.
- `Bar` is frozen: assigning `close` raises `dataclasses.FrozenInstanceError`.
- `dataclasses.fields(Bar)` names are exactly `symbol, ts, open, high, low, close, volume`.
- `IngestError("missing results", "AAPL")`: `str()` is `"missing results: AAPL"`, `.reason`
  and `.symbol` set.
- A payload without `results` → `IngestError` with `reason == "missing results"`.
- A row with `v == -1` → `IngestError` with `reason == "negative volume"`.
- `end < start` → `IngestError` with `reason == "empty range"`; the fake saw zero calls.
- Fake yields `VendorError(429)` then the sample → three bars, exactly two calls.
- Fake yields `VendorError(429)` four times, `retries=3` → `IngestError` `reason == "vendor
  429"`, exactly four calls.
- Fake yields `VendorError(500)` → `IngestError` `reason == "vendor 500"`, exactly one call.
- End to end: `fetch_bars("AAPL", date(2024, 3, 4), date(2024, 3, 6), client=fake)` → three
  bars; the fake saw path `/v2/aggs/ticker/AAPL/range/1/day/2024-03-04/2024-03-06` and params
  `{"adjusted": "true", "sort": "asc"}`; `caplog` holds one INFO record on `data.ingest` whose
  message is `event=data.ingest.fetch symbol=AAPL bars=3`.
- A row with `v == 0` is kept (D2 open — assumption: kept).

8. **Pitfalls and risks**

1. `t` is epoch milliseconds; treating it as seconds puts every bar in 1970. Converted in
   `parse.py` only.
2. A valid ticker on a holiday returns the no-`results` envelope (probe §8), indistinguishable
   from an unknown ticker; treated as `"missing results"` here. If that proves common the
   pipeline's calendar should skip holidays — not this section's concern.
3. The free tier allows 5 calls/minute; the retry loop does not sleep (pacing is the client's).

9. **Skills used**

- `project-structure` — module sizes and `configs.py` placement.

10. **Contract deviations**

None.

11. **Open questions**

- `OQ-data-ingest-1` (→ D2): are zero-volume bars kept? Designed against: kept.
