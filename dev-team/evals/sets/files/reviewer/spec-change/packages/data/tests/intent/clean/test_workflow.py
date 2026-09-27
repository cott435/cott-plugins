"""Intent tests for the clean workflow, end to end (design §4)."""

import pandas as pd

from data.clean.api import clean_bars


def test_dedupe_keeps_higher_volume(bars):
    """Design §4 step 2 (deviation 2026-09-24): duplicate bars keep the higher-volume row."""
    out = clean_bars(bars)
    tuesday = out[out["timestamp"] == pd.Timestamp("2026-03-03")]
    assert len(tuesday) == 1
    assert int(tuesday["volume"].iloc[0]) == 150


def test_zero_volume_rows_dropped(bars):
    """Design §4 step 3: a zero-volume day is filled like a missing one."""
    out = clean_bars(bars)
    thursday = out[out["timestamp"] == pd.Timestamp("2026-03-05")]
    assert len(thursday) == 1
    assert float(thursday["close"].iloc[0]) == 10.7
    assert int(thursday["volume"].iloc[0]) == 0


def test_gap_row_carries_previous_close(bars):
    """Design §4 step 4: a filled row carries the previous bar's close and volume 0."""
    out = clean_bars(bars)
    wednesday = out[out["timestamp"] == pd.Timestamp("2026-03-04")]
    assert len(wednesday) == 1
    assert float(wednesday["close"].iloc[0]) == 10.7
    assert int(wednesday["volume"].iloc[0]) == 0


def test_one_row_per_business_day(bars):
    """Design §4 step 4: one row per business day between the first and last bar."""
    out = clean_bars(bars)
    expected = pd.bdate_range("2026-03-02", "2026-03-06")
    assert list(out["timestamp"]) == list(expected)
