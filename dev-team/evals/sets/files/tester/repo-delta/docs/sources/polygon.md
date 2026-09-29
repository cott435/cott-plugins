# Source probe — polygon — api — 2026-09-22

Purpose: `data/ingest` fetches one symbol's daily aggregate bars for a date range.
Probe: polygon.probe.py · Sample: polygon.sample.json

1. **Access** — `Env var: DATA_VENDOR_KEY` — `valid`, free tier (5 calls/minute). Static key
   sent as the `apiKey` query parameter.

2. **Endpoints**

| endpoint | method | auth | params called | evidence | documented for |
|---|---|---|---|---|---|
| `/v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}` | GET | `apiKey` | `adjusted=true`, `sort=asc`, `limit=50000` | observed | daily aggregate bars |

3. **Observed schema** — `/v2/aggs/ticker/…` (from `polygon.sample.json`):

| field | type as returned | nullable seen | notes |
|---|---|---|---|
| `ticker` | str | no | echoes the request |
| `queryCount`, `resultsCount`, `count` | int | no | equal on a full page |
| `adjusted` | bool | no | |
| `status` | str | no | `"OK"` on success |
| `results` | list[object] | **absent** when `resultsCount` is 0 | see Quirks |
| `results[].t` | int | no | epoch **milliseconds**, 05:00 UTC for a US session |
| `results[].o`, `h`, `l`, `c` | float | no | |
| `results[].v` | int | no | share volume |
| `results[].vw` | float | no | volume-weighted price; not consumed |
| `results[].n` | int | no | trade count; not consumed |

4. **Pagination** — none observed under `limit=50000` for a one-year daily range.

5. **Rate limits and quotas** — documented 5 calls/minute on the free tier; a 429 was observed
   on the sixth call inside a minute, body `{"status":"ERROR","error":"..."}`.

6. **Error responses**

| endpoint | bad request made | status | envelope as returned |
|---|---|---|---|
| `/v2/aggs/ticker/…` | unknown ticker `ZZZZ` | 200 | `{"status":"OK","resultsCount":0,"queryCount":0}` — no `results` key |
| `/v2/aggs/ticker/…` | `apiKey` unset | 401 | `{"status":"ERROR","error":"Unknown API Key"}` |

7. **Write semantics** — not applicable; read only.

8. **Quirks** — a valid ticker with no session in range (a holiday) returns 200 with
   `resultsCount: 0` and **no `results` key**, the same envelope as an unknown ticker
   (observed). `t` is milliseconds, not seconds (observed).

9. **Sections served**

## data/ingest

Purpose: fetch one symbol's daily aggregate bars for a date range and parse them into `Bar`
rows. Needs only `/v2/aggs/ticker/{ticker}/range/1/day/{from}/{to}` (observed) and the fields
`results[].t`, `o`, `h`, `l`, `c`, `v`, plus the presence of `results` itself.
