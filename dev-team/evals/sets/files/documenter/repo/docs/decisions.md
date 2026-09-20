# Decisions

## D1 — which vendor tier does the daily pull assume?

Scope: `data`
Recommendation: the paid tier, for the 5-year history window.
Assumption if unanswered: free tier, 2 years.
Decision: paid tier.
Status: decided
Applied: `data/ingest` 2026-09-12

## D2 — do we keep raw vendor payloads after cleaning?

Scope: repo
Recommendation: keep 30 days.
Assumption if unanswered: keep everything.
Decision:
Status: open
Applied:
