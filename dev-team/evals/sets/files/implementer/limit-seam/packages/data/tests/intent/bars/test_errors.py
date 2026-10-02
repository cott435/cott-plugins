"""Intent tests for `BarsError` — Design §5 and the checks of §4 phase 1."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

import pytest

from data.bars import BarsError, build_bars
from data.ingest import Trade

START = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc)
FIVE = timedelta(minutes=5)
NAIVE = datetime(2026, 9, 1, 9, 10)


def test_bars_error_is_a_value_error() -> None:
    """Design §5 BarsError: a subclass of ValueError (repo contract, Shared conventions)."""
    assert issubclass(BarsError, ValueError)


def test_empty_symbol(rows: list[Trade]) -> None:
    """Design §4 phase 1, check 1."""
    with pytest.raises(BarsError, match="symbol is empty"):
        build_bars(
            rows, "  ", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
        )


def test_naive_window(rows: list[Trade]) -> None:
    """Design §4 phase 1, check 2."""
    with pytest.raises(BarsError, match="start and end must be timezone-aware"):
        build_bars(
            rows,
            "AAA",
            start=NAIVE,
            end=END,
            interval=FIVE,
            min_size=1,
            fill_gaps=False,
        )


def test_start_not_before_end(rows: list[Trade]) -> None:
    """Design §4 phase 1, check 3."""
    with pytest.raises(BarsError, match="start must be before end"):
        build_bars(
            rows, "AAA", start=END, end=END, interval=FIVE, min_size=1, fill_gaps=False
        )


def test_interval_not_positive(rows: list[Trade]) -> None:
    """Design §4 phase 1, check 4."""
    with pytest.raises(BarsError, match="interval must be positive"):
        build_bars(
            rows,
            "AAA",
            start=START,
            end=END,
            interval=timedelta(0),
            min_size=1,
            fill_gaps=False,
        )


def test_window_not_a_whole_number_of_intervals(rows: list[Trade]) -> None:
    """Design §4 phase 1, check 5."""
    with pytest.raises(BarsError, match="window is not a whole number of intervals"):
        build_bars(
            rows,
            "AAA",
            start=START,
            end=END,
            interval=timedelta(minutes=7),
            min_size=1,
            fill_gaps=False,
        )


def test_window_of_too_many_intervals(rows: list[Trade]) -> None:
    """Design §4 phase 1, check 6."""
    with pytest.raises(BarsError, match="window has more than 10000 intervals"):
        build_bars(
            rows,
            "AAA",
            start=START,
            end=START + timedelta(seconds=10_001),
            interval=timedelta(seconds=1),
            min_size=1,
            fill_gaps=False,
        )


def test_min_size_below_one(rows: list[Trade]) -> None:
    """Design §4 phase 1, check 7."""
    with pytest.raises(BarsError, match="min_size must be at least 1"):
        build_bars(
            rows,
            "AAA",
            start=START,
            end=END,
            interval=FIVE,
            min_size=0,
            fill_gaps=False,
        )


def test_the_first_failing_check_is_the_one_raised(rows: list[Trade]) -> None:
    """Design §4 phase 1: the checks run in the order listed."""
    with pytest.raises(BarsError, match="symbol is empty"):
        build_bars(
            rows, "", start=END, end=START, interval=FIVE, min_size=0, fill_gaps=False
        )


def test_a_bad_row_is_named_by_its_index(rows: list[Trade]) -> None:
    """Design §6: a message names the row's index, never its contents."""
    naive = [*rows[:3], Trade(NAIVE, "AAA", 10.0, 1, "buy")]
    with pytest.raises(BarsError, match=r"row 3: naive timestamp"):
        build_bars(
            naive,
            "AAA",
            start=START,
            end=END,
            interval=FIVE,
            min_size=1,
            fill_gaps=False,
        )
    side = [rows[0], Trade(rows[1].ts, "AAA", 10.5, 50, "hold")]
    with pytest.raises(BarsError, match=r"row 1: unknown side"):
        build_bars(
            side,
            "AAA",
            start=START,
            end=END,
            interval=FIVE,
            min_size=1,
            fill_gaps=False,
        )
    price = [Trade(rows[0].ts, "AAA", 0.0, 100, "buy")]
    with pytest.raises(BarsError, match=r"row 0: non-positive price"):
        build_bars(
            price,
            "AAA",
            start=START,
            end=END,
            interval=FIVE,
            min_size=1,
            fill_gaps=False,
        )


def test_a_row_of_the_symbol_outside_the_window_is_still_checked(
    rows: list[Trade],
) -> None:
    """Design §4 phase 1: the row checks apply inside the window or not."""
    early = [*rows, Trade(START - timedelta(hours=1), "AAA", 9.0, 10, "hold")]
    with pytest.raises(BarsError, match=r"row 9: unknown side"):
        build_bars(
            early,
            "AAA",
            start=START,
            end=END,
            interval=FIVE,
            min_size=1,
            fill_gaps=False,
        )


def test_a_row_of_another_symbol_is_not_checked(rows: list[Trade]) -> None:
    """Design §4 phase 1: a row of another symbol is skipped unchecked."""
    mixed = [*rows, Trade(NAIVE, "BBB", -1.0, 10, "hold")]
    bars = build_bars(
        mixed, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
    )
    assert len(bars) == 3
