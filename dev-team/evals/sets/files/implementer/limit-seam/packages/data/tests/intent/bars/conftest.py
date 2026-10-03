"""Fixtures for the `data/bars` intent tests, built from the documents only.

`Trade` is the shipped `data.ingest.Trade` (its README, Entry points). The window every test
uses is 09:00 to 09:30 UTC on 2026-09-01 in five-minute bars: six intervals. The rows are in
file order, which is not time order (the ingest README, Implementation notes).
"""

from __future__ import annotations

from datetime import datetime, timezone
from pathlib import Path

import pytest

from data.ingest import Trade

_UTC = timezone.utc


def _t(
    hour: int, minute: int, symbol: str, price: float, size: int, side: str
) -> Trade:
    return Trade(
        datetime(2026, 9, 1, hour, minute, tzinfo=_UTC), symbol, price, size, side
    )


@pytest.fixture
def rows() -> list[Trade]:
    """Nine rows; row 4 is a late print, row 2 another symbol, rows 7 and 8 outside the window."""
    return [
        _t(9, 1, "AAA", 10.0, 100, "buy"),
        _t(9, 3, "AAA", 10.5, 50, "sell"),
        _t(9, 2, "BBB", 99.0, 10, "buy"),
        _t(9, 7, "AAA", 10.2, 200, "buy"),
        _t(9, 4, "AAA", 9.8, 30, "sell"),
        _t(9, 21, "AAA", 10.4, 5, "buy"),
        _t(9, 22, "AAA", 10.6, 40, "sell"),
        _t(9, 30, "AAA", 11.0, 10, "buy"),
        _t(8, 59, "AAA", 9.0, 10, "buy"),
    ]


@pytest.fixture
def csv_path(tmp_path: Path) -> Path:
    """The nine rows above as the CSV `load_trades` reads."""
    lines = [
        "ts,symbol,price,size,side",
        "2026-09-01T09:01:00Z,AAA,10.0,100,buy",
        "2026-09-01T09:03:00Z,AAA,10.5,50,sell",
        "2026-09-01T09:02:00Z,BBB,99.0,10,buy",
        "2026-09-01T09:07:00Z,AAA,10.2,200,buy",
        "2026-09-01T09:04:00Z,AAA,9.8,30,sell",
        "2026-09-01T09:21:00Z,AAA,10.4,5,buy",
        "2026-09-01T09:22:00Z,AAA,10.6,40,sell",
        "2026-09-01T09:30:00Z,AAA,11.0,10,buy",
        "2026-09-01T08:59:00Z,AAA,9.0,10,buy",
    ]
    p = tmp_path / "trades.csv"
    p.write_text("\n".join(lines) + "\n")
    return p
