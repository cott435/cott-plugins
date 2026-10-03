# Source probe — barfeed — api — 2026-10-02

Purpose: the `data` package downloads daily price bars from this vendor (`source: api:barfeed`).
Probe script: `docs/sources/barfeed.probe.py`; sample responses: `docs/sources/barfeed.sample.json`.

## Access

reachable — `https://api.barfeed.example/v2`, HTTPS, JSON. Called 14 times on 2026-10-02 with
the analyst's "Research" plan key.

Header `X-Api-Key: <key>`; the key is read from `BARFEED_API_KEY`. A missing or wrong key
returns `401` with `{"error": "unauthorized"}` (observed).

## Endpoints

- `GET /v2/bars/daily?symbol=<S>&year=<YYYY>&adjusted=false` — every daily bar of one symbol
  in one calendar year, oldest first (observed). One request returns at most one year; there is
  no multi-symbol or multi-year form (documented, and `symbol=AAA,BBB` returned `400`, observed).
- `GET /v2/calendar?year=<YYYY>` — the exchange's trading days for a year (observed). Does not
  count against the daily quota (documented; the quota header did not move, observed).

## Observed schema

`GET /v2/bars/daily` returns `{"symbol": str, "year": int, "bars": [...]}`; each bar:

| field | declared | observed | null % | note |
|---|---|---|---|---|
| `d` | date `YYYY-MM-DD` | str | 0 | the trading date |
| `o` | number | float | 0 | open |
| `h` | number | float | 0 | high |
| `l` | number | float | 0 | low |
| `c` | number | float | 0 | close |
| `v` | integer | int, and float `0.0` on 3 rows of 3,271 | 0 | volume |

About 252 bars per symbol-year; a response is about 18 KB.

## Pagination

none — one response holds the whole year (observed up to 253 bars).

## Rate limits and quotas

- 5 requests per second; the sixth in a second returns `429` with `Retry-After: 1` (observed).
- 2,000 requests per day on the "Research" plan, reset at 00:00 UTC (documented). The
  remaining count is in the response header `X-Quota-Remaining` (observed: 1,986 after 14
  calls). At zero every bars request returns `429` with `Retry-After` set to the seconds until
  the reset (documented, not observed).
- No charge per request on this plan. The next plan up, "Desk", is 20,000 requests a day at
  USD 79 a month (documented); the analyst has not bought it.

## Error responses

- `400` `{"error": "bad_request", "detail": str}` — a malformed symbol or year (observed).
- `401` `{"error": "unauthorized"}` (observed).
- `404` `{"error": "unknown_symbol"}` — a symbol the vendor does not carry (observed).
- `429` `{"error": "rate_limited"}` with `Retry-After` (observed for the per-second limit).

## Quirks

- The last bar of a year is repeated as the first bar of the next year's response on 2 of the
  4 symbols tried (observed), so appending year files double-counts that day.
- A market holiday has a bar with `v` 0 and `o` = `h` = `l` = `c` = the previous close on 1 of
  the 4 symbols tried (observed: 2024-07-04).
- `v` is `0.0`, a float, on those rows and an int elsewhere (observed).
- Bars are unadjusted with `adjusted=false`: a 2-for-1 split shows as a halved price from one
  day to the next (documented; none fell inside the years probed).
- Only 13 symbol-years of the universe's 5,000 were read, so this list is what was seen, not
  what is there.

## Cost and time of a full pull

- The universe is 500 symbols × 10 years (2016–2025) = 5,000 requests, about 1.26 million bars
  and about 90 MB of JSON.
- At the daily quota of 2,000 requests a full pull takes 3 calendar days (2,000 + 2,000 +
  1,000). Within a day, at 5 requests per second, 2,000 requests take about 7 minutes.
- No money on the "Research" plan. A run that uses the whole day's quota leaves the analyst
  with no vendor calls until 00:00 UTC.
- A weekly refresh of the current year is 500 requests.

## Sections served

## data/download

Calls `GET /v2/bars/daily` for each symbol and year and keeps each response's rows as sent.
