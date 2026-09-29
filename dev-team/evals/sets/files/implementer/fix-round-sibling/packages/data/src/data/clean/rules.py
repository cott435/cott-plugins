"""Collapse exact duplicate `Trade` rows and sort them into a TradeTable.

`Trade` is unhashable (the ingest README), so duplicates are found by a tuple of the row's
fields rather than by `set(rows)`.
"""

from __future__ import annotations

import logging
from datetime import datetime

from data.ingest import Trade

log = logging.getLogger("data.clean")

Key = tuple[datetime, str, float, int, str]


class CleanError(ValueError):
    """A row whose `ts` is naive after ingest — reserved; never expected today."""


def _key(t: Trade) -> Key:
    """The five fields that make two rows exact duplicates."""
    return (t.ts, t.symbol, t.price, t.size, t.side)


def _dedupe(rows: list[Trade]) -> list[Trade]:
    """Collapse exact duplicates, keeping one row per key."""
    seen: set[Key] = set()
    out: list[Trade] = []
    for t in reversed(rows):
        k = _key(t)
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def _sort(rows: list[Trade]) -> list[Trade]:
    """Stable sort by `(ts, symbol)`; a new list."""
    return sorted(rows, key=lambda t: (t.ts, t.symbol))


def clean_trades(rows: list[Trade]) -> list[Trade]:
    """Return `rows` as a TradeTable: exact duplicates collapsed, sorted by `(ts, symbol)`.

    Args:
        rows: trades in file order, as `load_trades` returns them. Not mutated.

    Returns:
        A new list with no exact duplicates, sorted by `ts` then `symbol`.
    """
    log.info("clean", extra={"rows_in": len(rows)})
    out = _sort(_dedupe(rows))
    log.info(f"cleaned {len(out)} rows, dropped {len(rows) - len(out)}")
    return out
