"""End-to-end path for `data/clean` — Design §4, `daily` pipeline steps 1–2."""

from __future__ import annotations

from pathlib import Path

from data.clean import clean_trades
from data.ingest import load_trades


def test_csv_through_ingest_and_clean(csv_path: Path) -> None:
    """Design §4 workflow: load_trades then clean_trades yields a sorted, deduped table."""
    table = clean_trades(load_trades(csv_path))
    assert len(table) == 6
    hours = [t.ts.hour for t in table]
    assert hours == sorted(hours)
    assert hours[0] == 7
