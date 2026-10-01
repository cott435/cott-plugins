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

## D3 — are prices in `BarTable` the vendor's floats as returned, or rounded to 4 decimal places?

Scope: `data`
Raised by: /dev-team:plan-package data (interview)
Recommendation: round once, half-even, when the table is built.
Assumption if unanswered: rounded to 4 decimal places, half-even.
Decision:
Status: open
Applied:
