"""Unit tests for the clean rules on two-row frames."""

import pandas as pd

from data.clean import rules
from data.clean.calendar import trading_days


def _frame(rows):
    frame = pd.DataFrame(rows, columns=["symbol", "timestamp", "open", "high", "low", "close", "volume"])
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame


def test_dedupe_keeps_first():
    frame = _frame([("AAA", "2026-03-03", 1, 1, 1, 1.5, 10), ("AAA", "2026-03-03", 1, 1, 1, 2.5, 20)])
    out = rules.dedupe(frame)
    assert len(out) == 1 and float(out["close"].iloc[0]) == 1.5


def test_dedupe_keeps_both_symbols():
    frame = _frame([("AAA", "2026-03-03", 1, 1, 1, 1, 10), ("BBB", "2026-03-03", 1, 1, 1, 1, 20)])
    assert len(rules.dedupe(frame)) == 2


def test_drop_zero_volume_drops_rows():
    frame = _frame([("AAA", "2026-03-03", 1, 1, 1, 1, 0), ("AAA", "2026-03-04", 1, 1, 1, 1, 5)])
    out = rules.drop_zero_volume(frame)
    assert len(out) == 1 and int(out["volume"].iloc[0]) == 5


def test_fill_gaps_counts_inserted_rows():
    frame = _frame([("AAA", "2026-03-02", 1, 1, 1, 1, 5), ("AAA", "2026-03-04", 1, 1, 1, 2, 5)])
    out, filled = rules.fill_gaps(frame)
    assert filled == 1 and len(out) == 3


def test_trading_days_inclusive():
    index = trading_days(pd.Timestamp("2026-03-02"), pd.Timestamp("2026-03-04"))
    assert len(index) == 3
