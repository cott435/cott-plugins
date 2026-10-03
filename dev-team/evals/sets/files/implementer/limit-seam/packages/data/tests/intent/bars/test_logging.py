"""Intent tests for the three `INFO` lines of `build_bars` — Design §4 and §6."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone

import pytest

from data.bars import build_bars
from data.ingest import Trade

START = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc)
FIVE = timedelta(minutes=5)


def _line(caplog: pytest.LogCaptureFixture, message: str) -> logging.LogRecord:
    found = [r for r in caplog.records if r.name == "data.bars" and r.msg == message]
    assert len(found) == 1, f"expected one {message!r} line on logger data.bars"
    return found[0]


def test_selected_line_counts_rows_by_why_they_were_dropped(
    rows: list[Trade], caplog: pytest.LogCaptureFixture
) -> None:
    """Design §4 phase 1: rows_in, rows_out, dropped, and the three counts that add up to it."""
    with caplog.at_level(logging.INFO, logger="data.bars"):
        build_bars(
            rows,
            "AAA",
            start=START,
            end=END,
            interval=FIVE,
            min_size=10,
            fill_gaps=False,
        )
    line = _line(caplog, "selected")
    assert (line.rows_in, line.rows_out, line.dropped) == (9, 5, 4)
    assert (line.other_symbol, line.outside_window, line.too_small) == (1, 2, 1)


def test_aggregated_and_filled_lines(
    rows: list[Trade], caplog: pytest.LogCaptureFixture
) -> None:
    """Design §4 phases 2 and 3: intervals, then bars_out and filled."""
    with caplog.at_level(logging.INFO, logger="data.bars"):
        build_bars(
            rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=True
        )
    assert _line(caplog, "aggregated").intervals == 3
    line = _line(caplog, "filled")
    assert (line.bars_out, line.filled) == (6, 3)
