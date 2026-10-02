Mode: new

# Design — `data/bars`

Written 2026-09-30 by `dev-team:designer`. Run: `run-package data`.

## 1. Purpose and scope

Builds the **Bar** rows of one symbol over one time window from the `Trade` rows `ingest`
reads: fixed-width intervals, each with its open, high, low, close, volume-weighted price
and volumes. Owns nothing else — no file reading, no persistence, no trading calendar: the
window and the width are the caller's.

## 2. Inputs and outputs

| direction | name | type | from / to |
|---|---|---|---|
| in | `rows` | `list[Trade]` — any order, any symbols | `data/ingest` — `load_trades` (`packages/data/src/data/ingest/README.md`, Entry points) |
| in | `symbol` | `str` — the one symbol to build bars for | the caller |
| in | `start` | `datetime`, timezone-aware — the window's first instant, inclusive | the caller |
| in | `end` | `datetime`, timezone-aware — the window's end, exclusive | the caller |
| in | `interval` | `timedelta` — the width of one bar | the caller |
| in | `min_size` | `int` — a trade smaller than this is left out of every bar | the caller |
| in | `fill_gaps` | `bool` — whether an interval with no trade still gets a bar | the caller |
| out | the bars | `list[Bar]`, in time order | the `daily` pipeline, `analysis` |

Seven inputs, each a value of its own. None has a default: the pipeline and `analysis` state
all seven at every call.

`Trade` is `data.ingest.Trade` (its README); this section defines no row type for its input.

Upstream packages: none

## 3. Data model / internal contracts

`Bar` — `@dataclass(frozen=True, slots=True)`, the **Bar** shape of the repo contract, with
these fields in this order: `symbol: str`, `start: datetime`, `open: float`, `high: float`,
`low: float`, `close: float`, `vwap: float`, `volume: int`, `buy_volume: int`, `trades: int`.

No state, no tables, no settings (`configs.py` is not needed; the section has no
configuration).

**Module plan** — under `packages/data/src/data/bars/`:

| file | holds | defines (§5) |
|---|---|---|
| `__init__.py` | re-exports `build_bars`, `Bar`, `BarsError` | — |
| `builder.py` | `Bar`, `BarsError`, and `build_bars` with the three phases of §4 | `build_bars`, `Bar`, `BarsError` |

## 4. Workflow / pipeline

Serves the `daily` pipeline (contract §4), second step. `build_bars` runs three phases in
order; each works on what the one before it produced.

| step | trigger | action | output | failure |
|---|---|---|---|---|
| 1 — check and select | `build_bars(…)` is called | check the arguments that are not `rows`; walk `rows`, check each row of the symbol, keep the ones inside the window and at least `min_size`, counting the rest by why they were dropped; sort the kept rows by time | the selected trades, in time order | `BarsError` |
| 2 — aggregate | — | put each selected trade in its interval and accumulate that interval's prices and volumes | one **Bar** per interval that has a trade | none |
| 3 — fill | — | walk every interval of the window in order; emit the interval's bar, or a flat bar where `fill_gaps` asks for one | `list[Bar]` in time order | none |

**Phase 1 — check and select.** The arguments are checked in this order, and the first check
that fails raises `BarsError` with the message given:

1. `symbol` is empty or only whitespace — `symbol is empty`
2. `start` or `end` has no `tzinfo` — `start and end must be timezone-aware`
3. `start >= end` — `start must be before end`
4. `interval <= timedelta(0)` — `interval must be positive`
5. `(end - start) % interval` is not zero — `window is not a whole number of intervals`
6. the window has more than 10 000 intervals — `window has more than 10000 intervals`
7. `min_size < 1` — `min_size must be at least 1`

Then `rows` is walked in input order, each row with its index `i`, its 0-based position in
`rows`:

- a row of another symbol is skipped unchecked, and counted as `other_symbol`: it is not this
  call's to judge;
- a row of the symbol whose `ts` has no `tzinfo` raises `BarsError`, `row <i>: naive timestamp`;
- a row of the symbol whose `side` is neither `buy` nor `sell` raises `BarsError`,
  `row <i>: unknown side`;
- a row of the symbol whose `price` is zero or negative raises `BarsError`,
  `row <i>: non-positive price`;
- a row that passed and whose `ts` is not in `start <= ts < end` is dropped, and counted as
  `outside_window`;
- a row inside the window whose `size` is below `min_size` is dropped, and counted as
  `too_small`;
- every other row is kept.

The three row checks apply to every row of the symbol, inside the window or not. The kept
rows are sorted by `ts`; the sort is stable, so two trades at the same instant stay in input
order. `rows` itself is never mutated. One `INFO` line, message `selected`: `rows_in`
(`len(rows)`), `rows_out` (kept), `dropped` (`rows_in - rows_out`), and the three counts that
add up to it, `other_symbol`, `outside_window` and `too_small`.

**Phase 2 — aggregate.** A trade's interval index is `(ts - start) // interval`, and the bar
of index `k` has `start = start + k * interval`. Walking the selected trades in order:

- the first trade of an interval sets its `open`, `high`, `low` and `close` to the trade's
  price;
- each later trade raises `high` or lowers `low` when its price is beyond them, and sets
  `close`;
- `volume` is the sum of the interval's sizes, `buy_volume` the sum of the sizes of its `buy`
  trades, `trades` the number of trades;
- `vwap` is the sum of `price * size` over the interval divided by `volume`, rounded to 6
  decimal places.

One `INFO` line, message `aggregated`: `intervals` (how many intervals have a trade).

**Phase 3 — fill.** The window has `n = (end - start) // interval` intervals. Walking the
indexes `0 … n - 1` in order:

- an interval that has a bar emits it;
- an interval with no trade emits a **flat bar** when `fill_gaps` is true and a bar has
  already been emitted in this walk: `open`, `high`, `low`, `close` and `vwap` are all the
  `close` of the bar emitted just before it (which may itself be a flat bar), and `volume`,
  `buy_volume` and `trades` are 0;
- an interval with no trade before the window's first trade is never emitted, whatever
  `fill_gaps` says; with `fill_gaps` false no empty interval is emitted.

One `INFO` line, message `filled`: `bars_out` (bars returned), `filled` (flat bars among
them). The list is returned in time order.

## 5. Interfaces

| name | signature | consumed by | Public | error cases |
|---|---|---|---|---|
| `build_bars` | the seven inputs of §2, by those names → `list[Bar]`. Callers pass `rows` and `symbol` first and name every other input | the `daily` pipeline, `analysis` | yes | `BarsError` as phase 1 lists; no kept row returns `[]` |
| `Bar` | `@dataclass(frozen=True, slots=True)` — §3 | everyone | yes | — |
| `BarsError` | `class BarsError(ValueError)` | `surface` | no | — |

## 6. Error handling and logging

Logger `data.bars`. One `INFO` line per phase with the keys §4 names, `extra=` keys only (repo
contract, Shared conventions). A message names a row by its index, never by its contents.
`BarsError` is the one exception type this section raises. No retries.

## 7. Tests

Unit (`packages/data/tests/unit/bars/`): each argument check of phase 1; a row at exactly
`end` is counted `outside_window` and a row at exactly `start` is kept; two trades in one
interval give one bar with the second's price as `close`; a gap of two intervals with
`fill_gaps` gives two flat bars carrying the same `close`.

Intent (`packages/data/tests/intent/bars/`, the tester's): one file per §5 row plus a
workflow test that reads a small CSV through `load_trades` and builds its bars.

## 8. Pitfalls and risks

1. `end` is exclusive: a trade at exactly `end` belongs to the next window.
2. Input order is file order, not time order (the ingest README): `open` and `close` are the
   first and last trade **by time**, so the sort of phase 1 comes before any aggregation.
3. A flat bar copies the previous **emitted** bar's `close`, so a run of empty intervals
   carries one price forward; no flat bar exists before the first trade.
4. `vwap` is rounded once, after the division; rounding each product drifts.
5. `rows` belongs to the caller — `sorted()`, never `rows.sort()`.

## 9. Skills used

- `project-structure` — one module under the section path; no `configs.py` when there is no
  configuration; the size limits of §2.
- `python-style-guide` — docstrings, `from __future__ import annotations`, `extra=` logging.

## 10. Contract deviations

None.

## 11. Open questions

None.
