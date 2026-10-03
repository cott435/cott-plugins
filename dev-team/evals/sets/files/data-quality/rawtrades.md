# Source probe — rawtrades — stage — 2026-10-01

Purpose: clean — turn the raw trade prints `download` stored into trades the rest of the package can trust
Profile: rawtrades.profile.py · Examples: rawtrades.sample.json

## Access

Location: `.dev-team/data/rawtrades/input/trades-2026-09-14.parquet` — on disk. Parquet, 1.9 MB,
1 file.

## Provenance

- `data.download.download_trades` (section `download`, commit `a41c9e2`), one session day,
  2026-09-14, four symbols.
- Vendor probe: `docs/sources/tradefeed.md`.

## Shape

48,210 rows × 8 columns, one table. The whole data was scanned; no count below is from a sample.

## Observed schema

| column | dtype as loaded | declared dtype | null % | distinct | range or top-k | notes |
|---|---|---|---|---|---|---|
| `seq` | int64 | int | 0 | 48,210 | 1 … 48,210 | the line number in the vendor file; unique |
| `trade_id` | string | str | 0 | 48,114 | `T-000001` … `T-048114` | not unique, see C2 |
| `symbol` | string | str | 0 | 6 | AAPL, MSFT, NVDA, TSLA, ZVZZT, TEST | |
| `ts` | string | datetime with offset | 0 | 46,902 | 2026-09-14T08:02:11-04:00 … 2026-09-14T17:58:40-04:00 | ISO 8601, always `-04:00` |
| `price` | float64 | float | 0 | 9,318 | 0.0 … 912.44 | |
| `size` | int64 | int | 0 | 1,207 | -4,000 … 25,000 | negative on 212 rows |
| `side` | string | `B` or `S` | 0 | 3 | B, S, and the empty string | empty on the 212 rows whose size is negative |
| `venue` | string | str | 0 | 6 | XNAS, XNYS, ARCX, BATS, XOFF, and the empty string | |

## Duplicates and keys

- Exact-duplicate rows: 0.
- `seq`: unique.
- `trade_id`: not unique. 96 rows repeat a `trade_id` already seen at a lower `seq`.

## Checks

| check | rule | judged against | rows failing | of |
|---|---|---|---|---|
| C1 | `size` > 0 | contract shape `RawTrade.size` | 212 | 48,210 |
| C2 | no row with the same `trade_id` and a lower `seq` | contract shape `RawTrade.trade_id` (one row per trade) | 96 | 48,210 |
| C3 | `price` > 0 | contract shape `RawTrade.price` | 41 | 48,210 |
| C4 | 09:30:00 ≤ time of `ts` < 16:00:00, America/New_York | the calendar: the regular session of 2026-09-14 | 1,530 | 48,210 |
| C5 | `symbol` is in the universe | contract, **Package conventions**, the universe line | 18 | 48,210 |
| C6 | `size` is a multiple of 100 | project skill `trade-cleaning`, rule "round lots only" | 6,204 | 48,210 |
| C7 | `venue` is in the venue list | contract, **Package conventions**, the venue line | 11 | 48,210 |

No row fails more than one check. 8,112 rows fail a check; 40,098 pass all seven.

## Quirks

- K1 negative-size — checks C1; 212 of 48,210; the vendor writes a sell as a negative size and leaves `side` empty; proposed: repair (take the absolute value of `size`); D7; verified
- K2 duplicate-trade-id — checks C2; 96 of 48,210; a print re-sent by the vendor, identical to the first but for `seq`, the first row by `seq` being the good one; proposed: drop; D8; verified
- K3 zero-price — checks C3; 41 of 48,210; a placeholder print with `price` 0.0 and a real size; proposed: quarantine; no decision needed; verified
- K4 off-session — checks C4; 1,530 of 48,210; a real print before the open or after the close; proposed: flag; no decision needed; verified
- K5 unknown-symbol — checks C5; 18 of 48,210; the vendor's test symbols `ZVZZT` and `TEST`; proposed: quarantine; no decision needed; verified
- K6 odd-lot — checks C6; 6,204 of 48,210; a size that is not a multiple of 100; proposed: drop; D?; unverified

## Unexplained

6,215 of 8,112 failing rows are in no verified kind.

- 6,204 rows fail C6 alone: the rows of K6, rejected twice by the verify run (17 of 20 sampled rows C6 flags are ordinary odd-lot trades, valid by the vendor probe).
- 11 rows fail C7 alone: `venue` is the empty string.

## Expected and not found

- `trade-cleaning`, rule "no trade on a market holiday": no row; 2026-09-14 is a session day.
- `trade-cleaning`, rule "price within 20% of the previous close": not checkable: no previous close is on disk.

## Rounds

### Round 0

| check | rows failing |
|---|---|
| C1 | 212 |
| C2 | 96 |
| C3 | 41 |
| C4 | 1,530 |
| C5 | 18 |
| C6 | 6,204 |
| C7 | 11 |

## Cost and time of a full pass

4.1 s wall time, 210 MB peak memory, 48,210 rows scanned. No pull: the data was on disk.

## Sections served

## data/clean

Purpose: turn the raw trade prints `download` stored into trades the rest of the package can trust.

Round 0 — 2026-10-01 — commit none — pending verify
Round 0 — 2026-10-01 — commit none — revise: K6
Round 0 — 2026-10-01 — commit none — pending verify
Round 0 — 2026-10-01 — commit none — kinds: 6 (2 to decide)
