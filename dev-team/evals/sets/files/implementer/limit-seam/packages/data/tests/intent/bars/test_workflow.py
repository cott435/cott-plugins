"""End-to-end path for `data/bars` — Design §4, `daily` pipeline steps 1–2."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone
from pathlib import Path

from data.bars import build_bars
from data.ingest import load_trades


def test_csv_through_ingest_and_bars(csv_path: Path) -> None:
    """Design §4 workflow: load_trades then build_bars yields the window's bars in time order."""
    start = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    bars = build_bars(
        load_trades(csv_path),
        "AAA",
        start=start,
        end=start + timedelta(minutes=30),
        interval=timedelta(minutes=10),
        min_size=1,
        fill_gaps=True,
    )
    assert [b.start.minute for b in bars] == [0, 10, 20]
    assert [b.trades for b in bars] == [4, 0, 2]
    assert bars[1].close == bars[0].close == 10.2
