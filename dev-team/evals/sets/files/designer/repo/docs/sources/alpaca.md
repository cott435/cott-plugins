# alpaca — api — probed 2026-09-24

Probed by `dev-team:researcher` (probe) for `data/prices`. Script: `docs/sources/alpaca.probe.py`;
sample: `docs/sources/alpaca.sample.json` (two symbols, five trading days, scrubbed).

## Access

- Auth: static headers `APCA-API-KEY-ID` and `APCA-API-SECRET-KEY`, from `ALPACA_API_KEY`
  and `ALPACA_API_SECRET`. No token refresh. `observed`
- Base URL: `https://data.alpaca.markets/v2`. `observed`

## Endpoints

| endpoint | method | purpose | label |
|---|---|---|---|
| `/stocks/bars` | GET | daily bars for a list of symbols | `observed` |
| `/stocks/{symbol}/bars` | GET | daily bars for one symbol | `observed` |

Query parameters on `/stocks/bars`: `symbols` (comma-separated), `timeframe=1Day`, `start`,
`end` (RFC 3339), `limit` (≤ 10000), `page_token`, `adjustment` one of `raw | split |
dividend | all` (default `raw`), `feed` (`iex` on the free plan). `observed`

## Observed schema

`GET /stocks/bars?symbols=AAPL,MSFT&timeframe=1Day&start=2026-09-15&end=2026-09-19` —
response body, every field seen in the sample: `observed`

```json
{
  "bars": {
    "AAPL": [
      {"t": "2026-09-15T04:00:00Z", "o": 231.1, "h": 233.9, "l": 230.4, "c": 233.2,
       "v": 41230011, "n": 512334, "vw": 232.41}
    ]
  },
  "next_page_token": null
}
```

- `t` — RFC 3339 UTC, the session's start at 04:00Z.
- `o`, `h`, `l`, `c` — floats. `c` is the close **as adjusted by the `adjustment`
  parameter**; with the default `raw` it is unadjusted. There is no separate adjusted close
  field in any response: no `adjusted_close`, no `ac`, in either endpoint, with any
  `adjustment` value.
- `v` — int, share volume. `n` — int, trade count. `vw` — float, VWAP; `null` on a
  zero-volume session (seen once in the sample, a halted symbol).
- Symbols with no bars in range are absent from `bars`, not present with an empty list.

## Pagination

`next_page_token` string when more than `limit` bars remain; pass as `page_token`. `observed`

## Rate limits and quotas

200 requests/minute on the free plan; a `429` carries `Retry-After` in seconds. `observed`

## Error responses

- `401` `{"message": "unauthorized."}` on a bad key. `observed`
- `422` `{"message": "..."}` on a bad parameter (an unknown `adjustment` value was tried). `observed`
- `429` as above. `observed`
- `5xx` — `documented` only; none seen.

## Quirks

- `adjustment` defaults to `raw`; a client that wants adjusted closes must send
  `adjustment=all` (or `split`/`dividend`) and read `c`.
- `vw` can be `null`; `c` was never null in the sample.
- The free `iex` feed misses some tickers on low-volume days (absent, not empty).

## Changes since last probe

First probe.

## Sections served

### data/prices

Purpose (the contract row): fetch daily bars from Alpaca and yield `Bar` records with adjusted
closes. Needs: `GET /stocks/bars` with `timeframe=1Day`, `adjustment`, `start`, `end`,
`limit`, `page_token`; fields `t`, `o`, `h`, `l`, `c`, `v`. All `observed`.
