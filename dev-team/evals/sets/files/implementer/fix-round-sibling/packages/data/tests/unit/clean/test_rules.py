"""Unit tests for `data.clean.rules`."""

from __future__ import annotations

from datetime import datetime, timezone

from data.clean.rules import _dedupe, _sort, clean_trades
from data.ingest import Trade

_UTC = timezone.utc


def _t(hour: int, symbol: str = "AAA", side: str = "buy") -> Trade:
    return Trade(datetime(2026, 9, 1, hour, tzinfo=_UTC), symbol, 10.0, 1, side)


def test_dedupe_collapses_two_identical_rows() -> None:
    """Two rows with equal fields become one."""
    assert len(_dedupe([_t(9), _t(9)])) == 1


def test_sort_orders_an_out_of_order_pair() -> None:
    """A later row before an earlier one is put after it."""
    out = _sort([_t(10), _t(9)])
    assert [t.ts.hour for t in out] == [9, 10]


def test_clean_trades_empty() -> None:
    """An empty list returns an empty list."""
    assert clean_trades([]) == []


def test_clean_trades_does_not_mutate_input() -> None:
    """The caller's list is unchanged."""
    rows = [_t(10), _t(9), _t(9)]
    before = list(rows)
    clean_trades(rows)
    assert rows == before
