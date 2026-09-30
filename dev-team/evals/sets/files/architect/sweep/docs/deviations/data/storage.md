# Deviations — data/storage

## data/storage — 2026-09-25 — deviation

Clause: contract §3 storage `store_trades`
Said: "`store_trades(trades: list[Trade], db_path: Path) -> int` inserts with `INSERT OR IGNORE` and returns the number of rows inserted"
Did: `store_trades(trades: list[Trade], db_path: Path, batch_size: int = 500) -> int` — inserts in batches of `batch_size`
Why: a large export held the whole insert in one transaction
Status: approved
Raised by: implementer — run-package data
Resolved by: —
