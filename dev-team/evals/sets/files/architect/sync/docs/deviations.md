# Deviations and spec-changes — trade tape

## data/ingest — 2026-09-23 — deviation

Clause: contract §3 ingest `read_export`
Said: "raising `TradeParseError(row: int, field: str)` (a `DataError`) on the first bad row"
Did: proposed skipping a bad row with a warning and continuing, returning the good rows
Why: the analyst would rather see most of the tape than none of it
Status: rejected
Raised by: implementer — run-package data
Resolved by: docs/reviews/2026-09-23-data-ingest-r1-a.md (the brief says reject and say which; the run stops)

## data/clean — 2026-09-24 — deviation

Clause: contract §3 clean `dedupe`
Said: "`dedupe(trades: list[Trade]) -> list[Trade]` drops records equal on all five fields, keeping the first"
Did: `dedupe(trades: list[Trade]) -> tuple[list[Trade], int]` — the kept records and the number dropped; `clean_trades` unwraps it
Why: the pipeline logs how many duplicates the export carried, which the brief's analyst asked to see; the count is only known inside `dedupe`
Status: approved
Raised by: implementer — run-package data
Resolved by: —

## data/storage — 2026-09-25 — deviation

Clause: contract §3 storage `store_trades`
Said: "`store_trades(trades: list[Trade], db_path: Path) -> int` inserts with `INSERT OR IGNORE` and returns the number of rows inserted"
Did: `store_trades(trades: list[Trade], db_path: Path, batch_size: int = 500) -> int` — inserts in batches of `batch_size`
Why: a large export held the whole insert in one transaction
Status: approved
Raised by: implementer — run-package data
Resolved by: —
