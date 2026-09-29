# Decisions

## D1 — Which engine backs the bar store?

Scope: data/storage
Raised by: /dev-team:plan-repo (interview)
Recommendation: DuckDB, single file, path from `DATA_DB_PATH`.
Assumption if unanswered: DuckDB.
Decision: DuckDB. One file at `DATA_DB_PATH`; no server.
Status: decided
