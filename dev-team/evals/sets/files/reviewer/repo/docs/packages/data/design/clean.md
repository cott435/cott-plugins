Mode: new

# Design — `data/clean`

## 1. Purpose and scope

Turns the BarFrame `ingest.fetch_bars` returns into one bar per symbol per business day:
duplicates resolved, zero-volume days treated as missing, gaps filled. It does not fetch,
store, or adjust prices.

## 2. Inputs and outputs

- In: a BarFrame (repo contract, **Boundaries**) as `data.ingest.fetch_bars` returns it —
  columns `symbol, timestamp, open, high, low, close, volume` per the ingest README's
  **Entry points and interfaces**; timestamps naive UTC midnight; may hold duplicates and
  zero-volume rows; one or many symbols.
- Out: a BarFrame with the same columns and dtypes, sorted by `symbol, timestamp`.

## 3. Data model / internal contracts

No state. Internal constant `REQUIRED`: the seven BarFrame column names.

**Module plan**

| module | holds | lines (est.) |
|---|---|---|
| `api.py` | `clean_bars`, validation, the log event | 50 |
| `rules.py` | `dedupe`, `drop_zero_volume`, `fill_gaps` | 70 |
| `calendar.py` | `trading_days` | 15 |
| `errors.py` | `MissingColumns`, `EmptyBars` | 15 |

## 4. Workflow / pipeline

1. **Validate** — every `REQUIRED` column present, else `MissingColumns`; at least one row,
   else `EmptyBars`. Output: the input frame, untouched.
2. **Dedupe** — duplicate bars are the same `(symbol, timestamp)` pair (D1, decided).
   Duplicate bars are resolved by keeping the first row and dropping the rest.
3. **Drop zero-volume rows** — rows whose `volume` is 0 are dropped before gaps are filled,
   so a zero-volume day is filled like a missing one.
4. **Fill gaps** — per symbol, for every business day (Mon–Fri) between that symbol's first
   and last bar with no row, insert one whose `open`, `high`, `low` and `close` all equal
   the previous bar's `close` and whose `volume` is 0. Count the rows inserted.
5. **Log** — one `data.clean.done` event (§6) and return.

## 5. Interfaces

| name | signature | use | Public |
|---|---|---|---|
| `clean_bars` | `(df: DataFrame) -> DataFrame` | the `daily` pipeline; `features` | yes |
| `trading_days` | `(start: Timestamp, end: Timestamp) -> DatetimeIndex` | `fill_gaps` | no |

`clean_bars` never mutates its argument.

## 6. Error handling and logging

| case | behavior |
|---|---|
| a `REQUIRED` column absent | raise `MissingColumns(missing: list[str])` |
| `df` has no rows | raise `EmptyBars` |
| done | `log.info("data.clean.done", extra={rows_in, rows_out, gaps_filled})` |

Nothing is swallowed; no warnings.

## 7. Tests

Intent tests (fixture: a one-symbol week, Mon–Fri, with one duplicate and one zero-volume
day, built in `conftest.py`):

- `MissingColumns` on a frame lacking `volume`; `EmptyBars` on an empty frame.
- Output columns equal input columns; input not mutated.
- Dedupe keeps the first row; zero-volume rows are gone; a gap row carries the previous
  close and volume 0; the output has one row per business day.
- The `data.clean.done` event carries `rows_in`, `rows_out`, `gaps_filled`.

Unit tests cover each rule on a two-row frame.

## 8. Pitfalls and risks

1. Filling across the whole `min..max` span of a multi-symbol frame instead of per symbol
   would invent bars before a symbol's listing.
2. Filling from the previous row instead of the previous close would give a filled bar a
   high/low range that never traded.

## 9. Skills used

- `project-structure` — module placement and sizes.
- `python-style-guide` — docstrings, exceptions.

## 10. Contract deviations

None.

## 11. Open questions

- OQ-data-clean-1 → D1 (decided).
- OQ-data-clean-2 → D2 (open; designed against the assumption: no flag column).
