# Deviations — data/storage

## data/storage — 2026-09-27 — spec-change:test — 1

Clause: design §5 load_trades
Said: "Per contract §3." (contract §3: "`db_path` defaulting to `DATA_DB_PATH`")
Found: `packages/data/tests/intent/storage/test_store.py:17` passes the database path explicitly; no intent test calls `load_trades()` with no argument and `DATA_DB_PATH` set, so the default the contract states is untested
Why: the default is the only way `analysis` calls `load_trades`, and nothing checks it
Status: open
Raised by: reviewer — run-package data
Resolved by: —
