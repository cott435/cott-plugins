# Decisions

## D1 — Are timestamps stored as UTC or as read?

Scope: data
Raised by: /dev-team:plan-repo (interview)
Recommendation: UTC; a naive value is taken as UTC.
Assumption if unanswered: UTC.
Decision: UTC. A naive timestamp is taken as UTC.
Status: decided
Applied: data/ingest, 2026-09-23, packages/data/src/data/ingest/loader.py

## D2 — When a timestamp is written to disk, is it `Z` or `+00:00`?

Scope: repo
Raised by: /dev-team:plan-repo (interview)
Recommendation: `+00:00`, as `datetime.isoformat()` prints it; no custom formatting.
Assumption if unanswered: `+00:00`.
Decision:
Status: open
