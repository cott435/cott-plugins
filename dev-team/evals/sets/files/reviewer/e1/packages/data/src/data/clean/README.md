# `data/clean`

## Purpose

Turns the BarFrame `ingest.fetch_bars` returns into one bar per symbol per business day:
duplicates resolved, zero-volume days treated as missing, gaps filled.

## Files

| file | responsibility | used by |
|---|---|---|
| `api.py` | `clean_bars` and `CleanResult`: validation, the rules in order, the `data.clean.done` event | the `daily` pipeline, `features` |
| `rules.py` | `dedupe`, `drop_zero_volume`, `fill_gaps` | `api.py` |
| `calendar.py` | `trading_days` | `rules.py`; callers aligning to the fill calendar |
| `errors.py` | `MissingColumns`, `EmptyBars` | `api.py`, the `daily` pipeline |

## Entry points and interfaces

| name | signature | use | Public |
|---|---|---|---|
| `clean_bars` | `(df: DataFrame) -> CleanResult` | one clean BarFrame from a raw one, with its gap count | yes |
| `CleanResult` | `NamedTuple(bars: DataFrame, gaps_filled: int)` | what `clean_bars` returns | yes |
| `trading_days` | `(start: Timestamp, end: Timestamp) -> DatetimeIndex` | the index gaps are filled against | yes |

## Pipeline / workflow

1. validate (`api.py`) → 2. `dedupe` → 3. `drop_zero_volume` → 4. `fill_gaps` (`rules.py`,
   index from `calendar.py`) → 5. log and return a `CleanResult` (`api.py`). Step 2 of the
   `daily` pipeline.

## Configuration

None. The section reads no environment variable.

## Running and testing

`uv run pytest packages/data/tests/unit/clean packages/data/tests/intent/clean -q`

## Implementation notes

- The public `trading_days` and `CleanResult` are design §10 items 1 and 2, in
  `docs/packages/data/deviations/clean.md`.
- `fill_gaps` works per symbol so a late-listed symbol is not back-filled to the frame's
  earliest date (design §8 item 1).
