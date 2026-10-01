"""Fixtures for the surface section's intent tests (design §7)."""

from collections.abc import Callable
from datetime import date

import pandas as pd
import pytest

COLUMNS = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]


@pytest.fixture
def fetch() -> Callable[[str, date, date], pd.DataFrame]:
    """Stands in for the vendor: two days of bars per symbol, none for `NONE`."""

    def _fetch(symbol: str, start: date, end: date) -> pd.DataFrame:
        rows = [
            (symbol, "2026-03-05", 10.0, 10.5, 9.8, 10.2, 100),
            (symbol, "2026-03-06", 10.2, 10.9, 10.1, 10.7, 120),
        ]
        frame = pd.DataFrame([] if symbol == "NONE" else rows, columns=COLUMNS)
        frame["timestamp"] = pd.to_datetime(frame["timestamp"])
        return frame

    return _fetch
