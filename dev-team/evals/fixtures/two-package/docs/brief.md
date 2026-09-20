# Trade tape — brief
Status: ready
Updated: 2026-09-18

## Purpose
A small research tool for one analyst who has a CSV export of trades and wants a clean,
queryable copy of it plus a per-symbol VWAP summary they can paste into notes. Today they
clean the export by hand in a spreadsheet and get duplicates and mis-ordered rows wrong.

## Users and use
One analyst, from the command line, a few times a week, on a laptop. No service, no
scheduler, no network.

## Scope — now
| Area | Capability | Notes |
|---|---|---|
| data | load trades | Read `data/trades.csv` (columns `ts`, `symbol`, `price`, `size`, `side`; `ts` is ISO 8601 UTC). The file is the only input: `source: dataset:trades`. Reject a row with a missing or unparseable field, and say which. |
| data | clean trades | Drop exact duplicate rows and sort by `ts`. The export is known to contain duplicates and out-of-order rows. |
| data | store trades | Persist the clean trades to a local SQLite file with the standard library's `sqlite3`; re-running on the same input must not duplicate rows. |
| analysis | rolling VWAP | Rolling volume-weighted average price per symbol over a window the user sets, computed from the stored trades via the data package's `load_trades`. |
| analysis | summary report | A markdown summary: one row per symbol with trade count, total size, last price and last VWAP. |

## Scope — later
Not planned now; the design must not rule these out.
| Area | Capability | Notes |
|---|---|---|
| data | second export format | A Parquet export of the same columns. |

## Out of scope
- Live market data — the analyst works from exports only.
- Charts — the markdown table is enough.

## Constraints
- Python, managed with `uv`.
- Two packages: `data` (sections `ingest`, `clean`, `storage`, in that dependency order) and
  `analysis` (sections `features`, `report`; `report` depends on `features`). `analysis`
  depends on `data`.
- No third-party runtime dependencies beyond what the toolchain needs; SQLite through `sqlite3`.
- Timezone: UTC everywhere.
- Logging, config and CLI library: no preference.

## Known inputs
| Input | Kind | State |
|---|---|---|
| `data/trades.csv` — 400 synthetic rows, 3 symbols | data | exists |

## Success criteria
- `data` loads, cleans and stores the fixture: 398 rows stored, sorted by `ts`, and a second
  run stores nothing new.
- `analysis` prints a markdown summary with one row per symbol.

## Open questions
- none
