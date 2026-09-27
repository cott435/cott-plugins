"""End-to-end path for `data/storage` — Design §4, the `daily` pipeline."""

from __future__ import annotations

from pathlib import Path

from data.storage import read_trades, store_clean


def test_daily_path_is_sorted_and_deduped(csv_path: Path, db: Path) -> None:
    """Design §4 workflow: store_clean then read_trades yields a sorted, deduped table."""
    store_clean(csv_path, db)
    table = read_trades(db)
    hours = [t.ts.hour for t in table]
    assert hours == sorted(hours)
    assert hours[0] == 7
    assert len(table) == 6
