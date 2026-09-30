"""SQLite persistence for Trade records, idempotent on re-run."""

from __future__ import annotations

import os
import sqlite3
from datetime import datetime, timezone
from pathlib import Path

from data.ingest.model import Trade

_SCHEMA = """
CREATE TABLE IF NOT EXISTS trades (
    ts TEXT NOT NULL, symbol TEXT NOT NULL, price REAL NOT NULL,
    size INTEGER NOT NULL, side TEXT NOT NULL,
    UNIQUE (ts, symbol, price, size, side)
)
"""


def _db_path(db_path: Path | None) -> Path:
    return db_path or Path(os.environ.get("DATA_DB_PATH", "./trades.sqlite"))


def init_db(db_path: Path) -> None:
    """Create the trades table with a UNIQUE constraint over the five columns."""
    with sqlite3.connect(db_path) as conn:
        conn.execute(_SCHEMA)


def store_trades(trades: list[Trade], db_path: Path) -> int:
    """INSERT OR IGNORE every record; return the number of rows inserted."""
    init_db(db_path)
    rows = [(t.ts.isoformat(), t.symbol, t.price, t.size, t.side) for t in trades]
    with sqlite3.connect(db_path) as conn:
        before = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
        conn.executemany("INSERT OR IGNORE INTO trades VALUES (?, ?, ?, ?, ?)", rows)
        after = conn.execute("SELECT COUNT(*) FROM trades").fetchone()[0]
    return int(after - before)


def load_trades(db_path: Path | None = None) -> list[Trade]:
    """Every stored row sorted by ts; db_path defaults to DATA_DB_PATH."""
    path = _db_path(db_path)
    init_db(path)
    with sqlite3.connect(path) as conn:
        cur = conn.execute("SELECT ts, symbol, price, size, side FROM trades ORDER BY ts")
        return [
            Trade(
                ts=datetime.fromisoformat(ts).astimezone(timezone.utc),
                symbol=symbol,
                price=price,
                size=size,
                side=side,
            )
            for ts, symbol, price, size, side in cur.fetchall()
        ]
