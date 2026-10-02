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
    """Return `rows` without exact duplicates: the first row of each key, in input order."""
    seen: set[Key] = set()
    out: list[Trade] = []
    for t in rows:
        k = _key(t)
        if k not in seen:
            seen.add(k)
            out.append(t)
    return out


def clean_trades(rows: list[Trade]) -> list[Trade]:
    """Return `rows` as a TradeTable: exact duplicates collapsed, sorted by `(ts, symbol)`.

    Logs one `INFO` line `clean` with `rows_in` and one `cleaned` with `rows_out` and
    `dropped`.

    Args:
        rows: trades in file order, as `load_trades` returns them. Not mutated.

    Returns:
        A new list with no exact duplicates, sorted by `ts` then `symbol`.
    """
    log.info("clean", extra={"rows_in": len(rows)})
    # 1. collapse exact duplicates, first occurrence kept
    unique = _dedupe(rows)
    # 2. order by time, then symbol; ties keep file order
    out = sorted(unique, key=lambda t: (t.ts, t.symbol))
    log.info("cleaned", extra={"rows_out": len(out), "dropped": len(rows) - len(out)})
    return out
