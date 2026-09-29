"""Intent tests for `clean_trades` — Design §5, one per stated behavior."""

from __future__ import annotations

from data.clean import clean_trades
from data.ingest import Trade


def test_exact_duplicates_collapse(rows: list[Trade]) -> None:
    """Design §5 clean_trades: exact duplicate rows collapse to one."""
    out = clean_trades(rows)
    assert len(out) == 5
    assert sum(1 for t in out if t.symbol == "BBB" and t.ts.hour == 10) == 1


def test_sorted_by_ts_then_symbol(rows: list[Trade]) -> None:
    """Design §4 step 3: the result is sorted by (ts, symbol)."""
    out = clean_trades(rows)
    assert [(t.ts, t.symbol) for t in out] == sorted((t.ts, t.symbol) for t in out)
    assert out[0].symbol == "CCC"


def test_empty_input_returns_empty() -> None:
    """Design §5 clean_trades: an empty list returns an empty list."""
    assert clean_trades([]) == []


def test_input_is_not_mutated(rows: list[Trade]) -> None:
    """Design §4: the input list is never mutated; a new list is returned."""
    before = list(rows)
    out = clean_trades(rows)
    assert rows == before
    assert out is not rows
