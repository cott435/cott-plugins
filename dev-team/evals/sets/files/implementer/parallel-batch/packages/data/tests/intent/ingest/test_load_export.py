"""Intent tests for `load_export` — Design §5, one per stated behavior."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

from data.ingest import load_export


def test_rows_in_file_order_comments_skipped(export_path: Path) -> None:
    """Design §5 load_export: rows come back in file order; comment lines are not rows."""
    rows = load_export(export_path)
    assert [t.symbol for t in rows] == ["ABC", "XYZ", "ABC"]


def test_trade_time_converted_to_utc(export_path: Path) -> None:
    """Design §4 step 3: `ts` is parsed day first and converted to UTC (D1, D2)."""
    rows = load_export(export_path)
    assert rows[0].ts == datetime(2026, 9, 29, 7, 0, 0, tzinfo=timezone.utc)
    assert rows[0].ts.utcoffset() == timedelta(0)


def test_side_codes_and_quantity(export_path: Path) -> None:
    """Design §4 step 3: side codes map to buy/sell; a `'` separator in Qty is removed."""
    rows = load_export(export_path)
    assert [t.side for t in rows] == ["buy", "sell", "sell"]
    assert [t.size for t in rows] == [100, 1200, 50]
    assert rows[1].price == 20.25


def test_no_data_rows_returns_empty(make_export: Callable[[str, list[str]], Path]) -> None:
    """Design §5 load_export: a file with no data rows returns []."""
    p = make_export("empty.csv", ["# venue=XVEN", "TradeTime;Ticker;Px;Qty;Side"])
    assert load_export(p) == []
