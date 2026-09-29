# Decisions

## D1 — Which timezone are trade timestamps stored in?
Scope: repo
Raised by: /dev-team:plan-repo (interview)
Recommendation: UTC everywhere; convert only at the edges.
Assumption if unanswered: UTC.
Decision: UTC. Timestamps stay ISO 8601 strings with a `Z` suffix.
Status: decided
Applied:

## D2 — Are trade sizes integers or decimals?
Scope: data/ingest, data/clean
Raised by: /dev-team:plan-package data (interview)
Recommendation: Integers; the export has no fractional sizes.
Assumption if unanswered: Integers; a fractional size is a bad row.
Decision:
Status: open
Applied:
