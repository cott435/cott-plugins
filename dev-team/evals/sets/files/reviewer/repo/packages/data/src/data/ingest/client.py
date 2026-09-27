"""Vendor client: `fetch_bars` and its retry loop."""

from __future__ import annotations

import time
from datetime import date

import pandas as pd

from data.ingest.errors import VendorUnavailable

COLUMNS = ("symbol", "timestamp", "open", "high", "low", "close", "volume")


def fetch_bars(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Return the vendor's daily bars for `symbol` between `start` and `end` inclusive.

    Retries a 429 three times with a 0.5s back-off, then raises `VendorUnavailable`.
    The frame is returned as the vendor sent it: duplicates and zero-volume rows included.
    """
    for attempt in range(4):
        response = _get(symbol, start, end)
        if response.status != 429:
            return _to_frame(symbol, response.rows)
        if attempt < 3:
            time.sleep(0.5)
    raise VendorUnavailable(symbol)


def _get(symbol, start, end):  # pragma: no cover - network
    raise NotImplementedError


def _to_frame(symbol: str, rows: list[dict]) -> pd.DataFrame:
    frame = pd.DataFrame(rows)
    frame["symbol"] = symbol
    frame["timestamp"] = pd.to_datetime(frame["date"], utc=True).dt.tz_localize(None)
    return frame.loc[:, list(COLUMNS)]
