# Deviations and spec-changes

Append-only; status lines are the only edits.

## data/clean — 2026-09-24 — deviation

Clause: design §4 step 2 dedupe
Said: "duplicate bars are resolved by keeping the first row and dropping the rest"
Did: keeps the row with the higher `volume`; ties keep the first row
Why: the ingest README's **Implementation notes** say a bar the vendor returns twice in one
response is an end-of-day correction and the later row carries the corrected volume, so the
first row is the stale one.
Status: approved
Raised by: implementer — run-package data
Resolved by: docs/reviews/2026-09-23-data-clean-r1-a.md
