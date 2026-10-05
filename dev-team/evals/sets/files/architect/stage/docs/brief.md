# Bar store — brief
Status: ready
Updated: 2026-10-01

## Purpose
A small research tool for one analyst who wants ten years of daily price bars for a fixed
list of 500 US stocks in a local, queryable store, and a per-symbol return summary to paste
into notes. Today they download bars from the vendor by hand and find the bad rows — repeated
days, holiday bars, prices on the wrong side of a split — only when a backtest looks wrong.

## Users and use
One analyst, from the command line, once a week, on a laptop. No service and no scheduler.
The only network call is to the bar vendor.

## Scope — now
| Area | Capability | Notes |
|---|---|---|
| data | download bars | Call the Barfeed REST API for daily bars, one request per symbol and calendar year, for every symbol in `config/universe.txt`: `source: api:barfeed`. Append each response's rows, exactly as the vendor sent them, to `var/raw/bars/<symbol>.jsonl`. It checks the HTTP status and nothing else: a row is never read, changed or dropped here. |
| data | clean and validate bars | Read the raw bar files the download wrote and judge every row: `high` ≥ `open`, `close` ≥ `low`; prices above zero; volume zero or more; one bar per symbol and day; the day is a trading day. Rows that pass go on as the clean bars. A row that fails is set aside with the reason, never silently dropped. The vendor is known to repeat the last bar of a year in the next year's response and to send zero-volume bars on market holidays; nobody has looked at what else is in ten years of it. |
| data | store bars | Persist the clean bars it is handed to a local SQLite file with the standard library's `sqlite3`, exactly as received — no checking, no reshaping; re-running on the same input must not duplicate rows. Reads them back for `analysis`. |
| analysis | returns | Daily and trailing 21-day returns per symbol, computed from the stored bars via the data package's `load_bars`. |
| analysis | summary report | A markdown summary: one row per symbol with bar count, first and last day, last close and trailing return. |

## Scope — later
Not planned now; the design must not rule these out.
| Area | Capability | Notes |
|---|---|---|
| data | intraday bars | One-minute bars from the same vendor. |

## Out of scope
- Live quotes or streaming — the analyst works from end-of-day bars only.
- Charts — the markdown table is enough.
- Adjusting prices for splits and dividends — bars are stored as the vendor's `adjusted=false` rows.

## Constraints
- Python, managed with `uv`.
- Two packages: `data` (sections `download`, `clean`, `storage`, in that dependency order)
  and `analysis` (sections `features`, `report`; `report` depends on `features`). `analysis`
  depends on `data`.
- One third-party runtime dependency, `httpx`, for the vendor calls; SQLite through `sqlite3`.
- The vendor plan is the analyst's own "Research" plan; its limits are in
  `docs/sources/barfeed.md`.
- Timezone: UTC everywhere; a bar's `day` is the exchange's trading date.
- Logging, config and CLI library: no preference.

## Known inputs
| Input | Kind | State |
|---|---|---|
| Barfeed REST API, `GET /v2/bars/daily` | api | probed — `docs/sources/barfeed.md` |
| `config/universe.txt` — 500 symbols, one per line | config | exists |

## Success criteria
- `data` downloads, cleans and stores the universe: every stored bar passes every check, every
  failing row is kept with its reason, and a second run stores nothing new.
- `analysis` prints a markdown summary with one row per symbol.

## Open questions
- none
