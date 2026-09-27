"""The calendar the clean section fills gaps against."""

from __future__ import annotations

import pandas as pd


def trading_days(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Every day from `start` to `end` inclusive, at midnight."""
    return pd.date_range(start.normalize(), end.normalize(), freq="D", name="timestamp")
