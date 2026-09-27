"""Download raw bars from the vendor."""

import os
from datetime import date

import httpx
import pandas as pd

RAW_COLUMNS = ("ts", "open", "high", "low", "close", "volume")
VENDOR_URL = "https://vendor.example/v1/bars"


class VendorUnavailable(RuntimeError):
    """The vendor answered 429 three times in a row."""


def _fetch(symbol: str, start: date, end: date) -> list[dict]:
    key = os.environ["DATA_VENDOR_KEY"]
    params = {"symbol": symbol, "start": start.isoformat(), "end": end.isoformat()}
    for _attempt in range(3):
        response = httpx.get(VENDOR_URL, params=params, headers={"X-Key": key})
        if response.status_code != 429:
            response.raise_for_status()
            return response.json()["bars"]
    raise VendorUnavailable(symbol)


def load_bars(symbol: str, start: date, end: date) -> pd.DataFrame:
    """Raw bars for one symbol, one row per session, columns `RAW_COLUMNS`."""
    rows = _fetch(symbol, start, end)
    frame = pd.DataFrame(rows, columns=list(RAW_COLUMNS))
    frame["ts"] = pd.to_datetime(frame["ts"], utc=True)
    return frame
