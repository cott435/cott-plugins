"""Intent tests for data/storage."""

from datetime import datetime, timezone
from pathlib import Path

from data.ingest.model import Trade
from data.storage import load_trades, store_trades

T = Trade(datetime(2026, 9, 1, tzinfo=timezone.utc), "AAA", 1.0, 1, "buy")


def test_rerun_stores_nothing_new(tmp_path: Path):
    """Design §5 store_trades: a second run on the same input inserts 0 rows."""
    db = tmp_path / "t.sqlite"
    assert store_trades([T], db) == 1
    assert store_trades([T], db) == 0
    assert load_trades(db) == [T]
