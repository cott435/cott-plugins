# Decisions

## D1 — Which engine backs the bar store?

Scope: data/storage
Raised by: /dev-team:plan-repo (interview)
Recommendation: DuckDB, single file, path from `DATA_DB_PATH`.
Assumption if unanswered: DuckDB.
Decision: DuckDB. One file at `DATA_DB_PATH`; no server.
Status: decided

## D2 — Which `adjustment` does `fetch_bars` send to Alpaca?

Scope: data
Raised by: /dev-team:plan-package data (interview)
Recommendation: `all` — closes adjusted for splits and dividends, which is what the momentum signals in `analysis` are computed over.
Assumption if unanswered: `all`.
Status: open
