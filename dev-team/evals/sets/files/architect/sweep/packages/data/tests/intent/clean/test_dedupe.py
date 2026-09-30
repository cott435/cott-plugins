"""Intent tests for data/clean."""

from datetime import datetime, timezone

from data.clean import dedupe, sort_by_ts
from data.ingest.model import Trade

T = Trade(datetime(2026, 9, 1, tzinfo=timezone.utc), "AAA", 1.0, 1, "buy")


def test_dedupe_drops_exact_duplicates():
    """Design §5 dedupe (deviation data/clean — 2026-09-24): returns (kept, dropped)."""
    assert dedupe([T, T]) == ([T], 1)


def test_sort_keeps_input_order_on_equal_ts():
    """Design §5 sort_by_ts: records with equal ts keep their input order."""
    b = Trade(T.ts, "BBB", 2.0, 1, "sell")
    assert sort_by_ts([b, T]) == [b, T]
