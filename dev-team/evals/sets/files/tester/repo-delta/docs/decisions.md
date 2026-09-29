# Decisions

## D1 — are `Bar.ts` values tz-aware UTC or the exchange's local time?

Scope: `data/ingest`
Raised by: /dev-team:plan-package data (interview)
Recommendation: tz-aware UTC, converted once in `ingest`.
Assumption if unanswered: tz-aware UTC.
Decision: tz-aware UTC.
Status: decided
Applied:

## D2 — are bars with zero volume kept or dropped?

Scope: `data/ingest`
Raised by: OQ-data-ingest-1
Recommendation: keep them; `clean` can drop by rule later.
Assumption if unanswered: kept.
Decision:
Status: open
Applied:
