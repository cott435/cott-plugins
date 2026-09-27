# Deviations

## data/ingest — 2026-09-24 — deviation

Clause: §6 missing results
Said: a payload with no `results` key raises `IngestError(reason="missing results", symbol=symbol)`.
Did: `parse_bars` returns `()` for a payload with no `results` key and logs one WARNING record on the logger `data.ingest`, message `event=data.ingest.parse.empty symbol=<symbol>`; `fetch_bars` then logs its usual INFO record with `bars=0`.
Why: polygon returns the no-`results` envelope for a valid ticker on a market holiday (`docs/sources/polygon.md` §8), so raising aborted the `daily` pipeline on every holiday of the 2024 backfill; an empty day is not an ingest failure.
Status: approved
Raised by: implementer, Dev-Team-Run: run-package data
Resolved by: docs/reviews/2026-09-24-data-ingest-r1-a.md
