"""Intent tests for phase 3 of `build_bars` — Design §4, the flat bars `fill_gaps` asks for."""

from __future__ import annotations

from datetime import datetime, timedelta, timezone

from data.bars import build_bars
from data.ingest import Trade

START = datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
END = datetime(2026, 9, 1, 9, 30, tzinfo=timezone.utc)
FIVE = timedelta(minutes=5)


def test_fill_gaps_gives_every_interval_after_the_first_trade_a_bar(
    rows: list[Trade],
) -> None:
    """Design §4 phase 3: an empty interval after a bar gets a flat bar."""
    bars = build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=True
    )
    assert [b.start.minute for b in bars] == [0, 5, 10, 15, 20, 25]


def test_a_flat_bar_carries_the_previous_close(rows: list[Trade]) -> None:
    """Design §8 pitfall 3: a run of empty intervals carries one price forward."""
    bars = build_bars(
        rows, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=True
    )
    for flat in (bars[2], bars[3]):
        assert (flat.open, flat.high, flat.low, flat.close, flat.vwap) == (10.2,) * 5
        assert (flat.volume, flat.buy_volume, flat.trades) == (0, 0, 0)
    assert bars[5].close == 10.6
    assert bars[5].trades == 0


def test_no_flat_bar_before_the_first_trade() -> None:
    """Design §4 phase 3: an empty interval before the first trade is never emitted."""
    late = [Trade(START + timedelta(minutes=21), "AAA", 10.4, 5, "buy")]
    bars = build_bars(
        late, "AAA", start=START, end=END, interval=FIVE, min_size=1, fill_gaps=True
    )
    assert [b.start.minute for b in bars] == [20, 25]
    assert bars[0].trades == 1
