"""The calendar the clean section fills gaps against."""

from __future__ import annotations

import pandas as pd


def trading_days(start: pd.Timestamp, end: pd.Timestamp) -> pd.DatetimeIndex:
    """Every day from `start` to `end` inclusive, at midnight.

    Raises:
        ValueError: `end` is before `start`.
    """
    if end < start:
        raise ValueError(f"end {end.date()} is before start {start.date()}")
    return pd.date_range(start.normalize(), end.normalize(), freq="D", name="timestamp")
