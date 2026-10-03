"""Intent tests for `build_bars` — Design §5, one per stated behavior of §4.

Every call passes `rows` and `symbol` first and names the other five inputs, as Design §5
says callers do.
"""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from data.bars import build_bars
from data.ingest import Trade

START = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc)
FIVE = timedelta(minutes=5)


def _minute(bar_start: datetime) -> int:
    return bar_start.minute


def test_one_bar_per_interval_with_a_trade(rows: list[Trade]) -> None:
    """Design §4 phases 2 and 3: with `fill_gaps` false, only intervals with a trade give a bar."""
    bars = build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
    )
    assert [_minute(b.start) for b in bars] == [0, 5, 20]
    assert all(b.symbol == "AAA" for b in bars)
    assert bars[1].start == START + FIVE


def test_open_and_close_are_first_and_last_by_time(rows: list[Trade]) -> None:
    """Design §8 pitfall 2: the 09:04 late print closes the first bar though it is row 4."""
    first = build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
    )[0]
    assert (first.open, first.high, first.low, first.close) == (10.0, 10.5, 9.8, 9.8)


def test_volumes_and_trade_count(rows: list[Trade]) -> None:
    """Design §4 phase 2: volume, buy_volume and trades are sums over the interval."""
    first = build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
    )[0]
    assert (first.volume, first.buy_volume, first.trades) == (180, 100, 3)


def test_vwap_is_rounded_to_six_places(rows: list[Trade]) -> None:
    """Design §4 phase 2: vwap is sum(price * size) / volume, rounded to 6 places."""
    bars = build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
    )
    assert bars[0].vwap == 10.105556
    assert bars[1].vwap == 10.2
    assert bars[2].vwap == 10.577778


def test_start_is_inclusive_and_end_exclusive(rows: list[Trade]) -> None:
    """Design §8 pitfall 1: a trade at `start` is in the first bar; one at `end` is in none."""
    at_start = Trade(START, "AAA", 10.1, 1, "buy")
    bars = build_bars(
        [*rows, at_start],
        "AAA",
        start=START,
        end=END,
        interval=FIVE,
        min_size=1,
        fill_gaps=False,
    )
    assert bars[0].open == 10.1
    assert bars[0].trades == 4
    assert all(b.start < END for b in bars)
    assert sum(b.volume for b in bars) == 426


def test_min_size_leaves_small_trades_out(rows: list[Trade]) -> None:
    """Design §4 phase 1: a trade smaller than `min_size` is in no bar."""
    last = build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=10, fill_gaps=False
    )[-1]
    assert _minute(last.start) == 20
    assert (last.open, last.close, last.volume, last.buy_volume, last.trades) == (
        10.6,
        10.6,
        40,
        0,
        1,
    )


def test_only_the_symbol_asked_for(rows: list[Trade]) -> None:
    """Design §4 phase 1: rows of another symbol are skipped; no kept row returns []."""
    other = build_bars(
        rows, "BBB", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
    )
    assert [(b.symbol, b.open, b.volume) for b in other] == [("BBB", 99.0, 10)]
    assert (
        build_bars(
            rows, "ZZZ", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=True
        )
        == []
    )


def test_trades_at_the_same_instant_keep_input_order() -> None:
    """Design §4 phase 1: the sort is stable, so the first of two tied rows opens the bar."""
    at = START + timedelta(minutes=1)
    tied = [Trade(at, "AAA", 10.0, 1, "buy"), Trade(at, "AAA", 10.3, 1, "sell")]
    bar = build_bars(
        tied, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=False
    )[0]
    assert (bar.open, bar.close) == (10.0, 10.3)


def test_rows_is_not_mutated(rows: list[Trade]) -> None:
    """Design §8 pitfall 5: the caller's list is left as it was."""
    before = list(rows)
    build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=True
    )
    assert rows == before
