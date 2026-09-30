"""Fixtures for the `data/clean` intent tests, built from the documents only.

`Trade` is the shipped `data.ingest.Trade` (its README, Entry points). Rows: six trades,
two of them exact duplicates, one out of time order.
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from data.ingest import Trade

_UTC = timezone.utc


def _t(hour: int, symbol: str, price: float, size: int, side: str) -> Trade:
    return Trade(datetime(2026, 9, 1, hour, 0, tzinfo=_UTC), symbol, price, size, side)


@pytest.fixture
def rows() -> list[Trade]:
    """Six rows: rows 2 and 4 are identical; row 5 (07:00) is out of order."""
    return [
        _t(9, "AAA", 10.0, 100, "buy"),
        _t(10, "BBB", 20.5, 50, "sell"),
        _t(11, "AAA", 10.5, 10, "sell"),
        _t(10, "BBB", 20.5, 50, "sell"),
        _t(7, "CCC", 5.25, 200, "buy"),
        _t(12, "AAA", 11.0, 30, "buy"),
    ]


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    """An eight-row CSV: two exact duplicate rows and one out-of-order timestamp."""
    lines = [
        "ts,symbol,price,size,side",
        "2026-09-01T09:00:00Z,AAA,10.0,100,buy",
        "2026-09-01T10:00:00Z,BBB,20.5,50,sell",
        "2026-09-01T10:00:00Z,BBB,20.5,50,sell",
        "2026-09-01T11:00:00Z,AAA,10.5,10,sell",
        "2026-09-01T07:00:00Z,CCC,5.25,200,buy",
        "2026-09-01T12:00:00Z,AAA,11.0,30,buy",
        "2026-09-01T12:00:00Z,AAA,11.0,30,buy",
        "2026-09-01T13:00:00Z,BBB,21.0,5,buy",
    ]
    p = tmp_path / "trades.csv"
    p.write_text("\n".join(lines) + "\n")
    return p
