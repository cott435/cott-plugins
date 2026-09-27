"""Fixtures for the clean section's intent tests, built from the design's §7 fixture."""

import pandas as pd
import pytest


@pytest.fixture
def bars() -> pd.DataFrame:
    """One symbol, the week of 2026-03-02: Mon, Tue (twice), Thu (volume 0), Fri.

    Wednesday is missing. The duplicate Tuesday differs only in volume; the zero-volume Thursday closes at 10.4.
    """
    rows = [
        ("AAA", "2026-03-02", 10.0, 10.5, 9.8, 10.2, 100),
        ("AAA", "2026-03-03", 10.2, 10.9, 10.1, 10.7, 120),
        ("AAA", "2026-03-03", 10.2, 10.9, 10.1, 10.7, 150),
        ("AAA", "2026-03-05", 10.4, 10.4, 10.4, 10.4, 0),
        ("AAA", "2026-03-06", 10.6, 11.0, 10.4, 10.9, 90),
    ]
    frame = pd.DataFrame(rows, columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame
