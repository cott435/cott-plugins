# Deviations — data/ingest

## data/ingest — 2026-09-23 — deviation

Clause: contract §3 ingest `read_export`
Said: "raising `TradeParseError(row: int, field: str)` (a `DataError`) on the first bad row"
Did: proposed skipping a bad row with a warning and continuing, returning the good rows
Why: the analyst would rather see most of the tape than none of it
Status: rejected
Raised by: implementer — run-package data
Resolved by: docs/reviews/2026-09-23-data-ingest-r1-a.md (the brief says reject and say which; the run stops)
