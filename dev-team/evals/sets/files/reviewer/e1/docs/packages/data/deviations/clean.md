# Deviations — data/clean

## data/clean — 2026-09-25 — deviation — 1

Clause: contract §Section interfaces clean — exported names
Said: "`clean`: `clean_bars(df: DataFrame) -> DataFrame` — the BarFrame `ingest.fetch_bars`
returns, with the same columns, one row per `(symbol, timestamp)`, one row per business day
between the first and last bar of each symbol."
Did: the section also exports `trading_days(start: Timestamp, end: Timestamp) ->
DatetimeIndex`, marked `Public: yes` in design §5 and the README; no consumer calls it yet
Why: a caller that aligns its own frame to the days `clean_bars` fills needs the same calendar;
exporting the one the section already has keeps the two from drifting. Nothing that calls
`clean_bars` changes.
Status: proposed
Raised by: designer — run-package data
Resolved by: —

## data/clean — 2026-09-25 — deviation — 2

Clause: contract §Section interfaces clean — clean_bars return type
Said: "`clean`: `clean_bars(df: DataFrame) -> DataFrame` — the BarFrame `ingest.fetch_bars`
returns, with the same columns, one row per `(symbol, timestamp)`, one row per business day
between the first and last bar of each symbol."
Did: `clean_bars(df: DataFrame) -> CleanResult`, a `NamedTuple(bars: DataFrame, gaps_filled:
int)`; the cleaned BarFrame is `result.bars`
Why: `features` weights filled days lower and today has to recount them from `volume == 0`;
returning the count `fill_gaps` already has saves that second pass.
Status: proposed
Raised by: designer — run-package data
Resolved by: —
