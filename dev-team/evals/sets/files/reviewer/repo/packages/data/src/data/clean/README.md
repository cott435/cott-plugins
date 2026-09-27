# `data/clean`

## Purpose

Turns the BarFrame `ingest.fetch_bars` returns into one bar per symbol per business day:
duplicates resolved, zero-volume days handled, gaps filled.

## Files

| file | responsibility | used by |
|---|---|---|
| `api.py` | `clean_bars`: validation, the rules in order, the `data.clean.done` event | the `daily` pipeline, `features` |
| `rules.py` | `dedupe`, `drop_zero_volume`, `fill_gaps` | `api.py` |
| `calendar.py` | `trading_days` | `rules.py` |
| `errors.py` | `MissingColumns`, `EmptyBars` | `api.py`, the `daily` pipeline |

## Entry points and interfaces

| name | signature | use | Public |
|---|---|---|---|
| `clean_bars` | `(df: DataFrame) -> DataFrame` | one clean BarFrame from a raw one | yes |
| `trading_days` | `(start: Timestamp, end: Timestamp) -> DatetimeIndex` | the index gaps are filled against | no |

## Pipeline / workflow

1. validate (`api.py`) → 2. `dedupe` → 3. `drop_zero_volume` → 4. `fill_gaps` (`rules.py`,
   index from `calendar.py`) → 5. log and return (`api.py`). Step 2 of the `daily` pipeline.

## Configuration

None. The section reads no environment variable.

## Running and testing

`uv run pytest packages/data/tests/unit/clean packages/data/tests/intent/clean -q`

## Implementation notes

- Dedupe keeps the higher-volume row rather than the first: docs/deviations.md, data/clean
  2026-09-24.
- Zero-volume rows are kept rather than dropped: docs/deviations.md, data/clean 2026-09-25.
- `fill_gaps` works per symbol so a late-listed symbol is not back-filled to the frame's
  earliest date (design §8 item 1).
