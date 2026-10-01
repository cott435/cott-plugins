# Decisions

## D1 — Are timestamps stored as UTC or as read?

Scope: data
Raised by: /dev-team:plan-repo (interview)
Recommendation: UTC; a naive value is taken as UTC.
Assumption if unanswered: UTC.
Decision: UTC. A naive timestamp is taken as UTC.
Status: decided
Applied: data/ingest, 2026-09-23, packages/data/src/data/ingest/loader.py

## D2 — Does `side` count when two rows are compared as exact duplicates?

Scope: data/clean
Raised by: OQ-data-clean-1
Recommendation: yes — all five fields. The venue repeats a row byte for byte; a buy and a sell at the same time, price and size are two trades, and dropping one loses volume.
Assumption if unanswered: yes; two rows are exact duplicates only when `ts`, `symbol`, `price`, `size` and `side` are all equal.
Decision:
Status: open

## D3 — When a timestamp is written to disk, is it `Z` or `+00:00`?

Scope: data
Raised by: /dev-team:plan-package data (interview)
Recommendation: `+00:00`, as `datetime.isoformat()` prints it; no custom formatting.
Assumption if unanswered: `+00:00`.
Decision:
Status: open
