# data/clean

Shipped 2026-09-25 (review round 2, approved).

## Purpose

Drop the bars that cannot be trusted before they are stored: a bar whose prices contradict
each other, a bar with a negative volume, and a repeat of a bar already seen. Changes no bar
and stores nothing.

## Files

- `filters.py` — `clean_bars` and the three checks it applies.
- `errors.py` — `CleanError(DataError)`.
- `__init__.py` — empty.

## Entry points and interfaces

| name | signature | Public | consumed by |
|---|---|---|---|
| `clean_bars` | `clean_bars(bars: Sequence[Bar]) -> list[Bar]` | no | `ingest_csv` pipeline |
| `CleanError` | `CleanError(DataError)`, code `data.clean.nothing_left` | no | callers of `clean_bars` |

`Bar` is `ingest`'s (`packages/data/src/data/ingest/README.md`); `clean` reads its fields and
builds no bar of its own.

## Pipeline / workflow

For each bar, in the order given: the price check (`low <= min(open, close)` and
`max(open, close) <= high`) → the volume check (`volume >= 0`) → the duplicate check (the
first bar of each (`symbol`, `ts`) is kept). A bar that fails one is dropped and logged at
`warning` with the check's name and the bar's `symbol`. The bars that pass are returned in
the order given. An empty input returns an empty list; an input that was not empty and of
which nothing is left raises `CleanError` (`data.clean.nothing_left`).

## Configuration

None.

## Running and testing

`uv run pytest tests/intent/clean tests/unit/clean` — 11 intent, 7 unit, all green.

## Implementation notes

- The duplicate check keeps a set of (`symbol`, `ts`) seen so far; memory is one tuple per
  bar kept.
