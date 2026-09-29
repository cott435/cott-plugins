# Deviations — data/clean

## data/clean — 2026-09-24 — deviation

Clause: contract §3 clean `dedupe`
Said: "`dedupe(trades: list[Trade]) -> list[Trade]` drops records equal on all five fields, keeping the first"
Did: `dedupe(trades: list[Trade]) -> tuple[list[Trade], int]` — the kept records and the number dropped; `clean_trades` unwraps it
Why: the pipeline logs how many duplicates the export carried, which the brief's analyst asked to see; the count is only known inside `dedupe`
Status: approved
Raised by: implementer — run-package data
Resolved by: —
