# Change — page-limit
Status: open

Written 2026-09-27 by /dev-team:plan-package data.

1. **Change goal**

`fetch_bars` asks polygon for one full page. Without `limit`, polygon's default page is 5000
aggregates, and the `features` backfill found two symbols whose ten-year ranges came back cut
off with no error. The probe already calls with `limit=50000` (`docs/sources/polygon.md` §2),
which covers any daily range this package requests in one page.

2. **Affected sections**

- `data/ingest` — `fetch_bars` sends `limit=50000` with its request; nothing else changes.

3. **Contract changes**

**Package contract: data**

- Changed: `fetch_bars(symbol, start, end, *, client, retries=3) -> tuple[Bar, ...]` — the
  signature is unchanged; the `params` it passes to `client.get` change from
  `{"adjusted": "true", "sort": "asc"}` to `{"adjusted": "true", "sort": "asc", "limit": "50000"}`.

4. **Downstream impact**

| consumer | shipped or planned | names affected | what breaks |
|---|---|---|---|
| `data/clean` | planned | `fetch_bars` | nothing: the return shape is unchanged |
| the `daily` pipeline | planned | `fetch_bars` | nothing: one call per symbol, as before |
