# Deviations — data/clean

## data/clean — 2026-09-24 — deviation

Clause: design §4 step 2 dedupe
Said: "duplicate bars are resolved by keeping the first row and dropping the rest"
Did: keeps the row with the higher `volume`; ties keep the first row
Why: the ingest README's **Implementation notes** say a bar the vendor returns twice in one
response is an end-of-day correction and the later row carries the corrected volume, so the
first row is the stale one. The intent test `test_workflow.py::test_dedupe_keeps_first` fails
by design until the tester regenerates it.
Status: approved
Raised by: implementer — run-package data
Resolved by: docs/packages/data/reviews/clean/2026-09-26-r1-a.md

## data/clean — 2026-09-25 — deviation

Clause: design §4 step 3 zero-volume rows
Said: "rows whose `volume` is 0 are dropped before gaps are filled, so a zero-volume day is
filled like a missing one"
Did: rows with `volume == 0` are kept as they came from the vendor
Why:
Status: rejected
Raised by: implementer — run-package data
Resolved by: docs/packages/data/reviews/clean/2026-09-26-r1-a.md
