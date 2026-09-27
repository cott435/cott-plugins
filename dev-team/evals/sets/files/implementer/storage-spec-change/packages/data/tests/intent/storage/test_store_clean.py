"""Intent test for `store_clean` — Design §5."""

from __future__ import annotations

from pathlib import Path

from data.storage import read_trades, store_clean


def test_store_clean_returns_rows_inserted(csv_path: Path, db: Path) -> None:
    """Design §5 store_clean: load, clean, store; returns rows inserted."""
    assert store_clean(csv_path, db) == 6
    assert len(read_trades(db)) == 6
