"""Intent tests for analysis/features, written from the design and the contracts."""

from datetime import datetime, timezone

import pytest

from analysis.errors import AnalysisError
from analysis.features import rolling_vwap
from data.ingest import Trade


def _t(minute: int, symbol: str, price: float, size: int) -> Trade:
    return Trade(datetime(2026, 9, 1, 13, minute, tzinfo=timezone.utc), symbol, price, size, "buy")


def test_window_of_two():
    """Design §5 rolling_vwap: each point is the VWAP of its symbol's last `window` trades."""
    points = rolling_vwap([_t(0, "AAA", 10.0, 1), _t(1, "AAA", 20.0, 1), _t(2, "AAA", 30.0, 3)], 2)
    assert [p.vwap for p in points] == pytest.approx([10.0, 15.0, 27.5])


def test_symbols_keep_their_own_window():
    """Design §5 rolling_vwap: two symbols never share a window."""
    points = rolling_vwap([_t(0, "AAA", 10.0, 1), _t(1, "BBB", 50.0, 1), _t(2, "AAA", 20.0, 1)], 5)
    assert [p.vwap for p in points] == pytest.approx([10.0, 50.0, 15.0])


def test_window_below_one_raises():
    """Design §6 AnalysisError: window < 1 raises."""
    with pytest.raises(AnalysisError):
        rolling_vwap([], 0)
