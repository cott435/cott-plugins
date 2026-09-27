"""Intent tests for `store_trades` and `read_trades` — Design §5."""

from __future__ import annotations

from datetime import timezone
from pathlib import Path

import pytest

from data.ingest import Trade
from data.storage import StorageError, read_trades, store_trades


def test_store_returns_rows_inserted(rows: list[Trade], db: Path) -> None:
    """Design §5 store_trades: returns the number of rows inserted."""
    assert store_trades(rows, db) == 5


def test_store_is_idempotent(rows: list[Trade], db: Path) -> None:
    """Design §3: INSERT OR IGNORE — a second store of the same rows inserts nothing."""
    store_trades(rows, db)
    assert store_trades(rows, db) == 0
    assert len(read_trades(db)) == 5


def test_read_round_trips_a_trade_table(rows: list[Trade], db: Path) -> None:
    """Design §5 read_trades: the table comes back sorted, with aware UTC timestamps."""
    store_trades(rows, db)
    out = read_trades(db)
    assert out == rows
    assert all(t.ts.tzinfo is not None and t.ts.utcoffset() == timezone.utc.utcoffset(None) for t in out)


def test_read_missing_file_raises(db: Path) -> None:
    """Design §5 read_trades: a missing db raises StorageError."""
    with pytest.raises(StorageError):
        read_trades(db)
