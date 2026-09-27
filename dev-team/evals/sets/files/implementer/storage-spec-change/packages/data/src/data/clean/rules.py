"""Dedupe and sort `Trade` rows into a TradeTable."""

from __future__ import annotations

import logging
from dataclasses import dataclass
from datetime import timezone

from data.ingest import Trade

log = logging.getLogger("data.clean")


class CleanError(ValueError):
    """A row reached clean with a naive timestamp."""


@dataclass(frozen=True, slots=True)
class CleanResult:
    """The table plus how many rows were dropped as duplicates."""

    rows: list[Trade]
    dropped: int


def _key(t: Trade) -> tuple[object, ...]:
    return (t.ts, t.symbol, t.price, t.size, t.side)


def _dedupe(rows: list[Trade]) -> list[Trade]:
    """Keep the first of each group of rows with identical fields."""
    seen: set[tuple[object, ...]] = set()
    out: list[Trade] = []
    for t in rows:
        if t.ts.tzinfo is None:
            raise CleanError("naive timestamp reached clean")
        k = _key(t)
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def clean_trades(rows: list[Trade]) -> CleanResult:
    """Collapse exact duplicates and sort by (ts, symbol).

    Args:
        rows: trades in any order, as `load_trades` returns them.

    Returns:
        A `CleanResult`: `rows` is the TradeTable, `dropped` the duplicate count.

    Raises:
        CleanError: a row's `ts` is naive.
    """
    log.info("clean start", extra={"rows_in": len(rows)})
    unique = _dedupe(rows)
    table = sorted(unique, key=lambda t: (t.ts.astimezone(timezone.utc), t.symbol))
    dropped = len(rows) - len(table)
    log.info("clean done", extra={"rows_out": len(table), "dropped": dropped})
    return CleanResult(rows=table, dropped=dropped)
