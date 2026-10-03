"""Write every symbol in its canonical form and sort the rows into a TradeTable.

The rows arrive from `ingest` with their repeats already dropped (contract, Package
conventions); nothing is deduplicated here.
"""

from __future__ import annotations

import dataclasses
import logging

from data.ingest import Trade

log = logging.getLogger("data.clean")


class CleanError(ValueError):
    """A row whose `ts` is naive after ingest — reserved; never expected today."""


def normalise_symbol(raw: str) -> str:
    """Return the canonical form of the symbol `raw`: stripped and upper-case."""
    return raw.strip().upper()


def clean_trades(rows: list[Trade]) -> list[Trade]:
    """Return `rows` as a TradeTable: every symbol canonical, sorted by `(ts, symbol)`.

    Logs one `INFO` line `clean` with `rows_in` and one `cleaned` with `rows_out`.

    Args:
        rows: trades in file order with their repeats already dropped, as `load_trades`
            returns them. Neither the list nor its rows are mutated.

    Returns:
        A new list of new rows, each symbol in its canonical form, sorted by `ts` then
        `symbol`.
    """
    log.info("clean", extra={"rows_in": len(rows)})
    # 1. normalise: one spelling per symbol
    canonical = [
        dataclasses.replace(t, symbol=normalise_symbol(t.symbol)) for t in rows
    ]
    # 2. order by time, then symbol; ties keep file order
    out = sorted(canonical, key=lambda t: (t.ts, t.symbol))
    log.info("cleaned", extra={"rows_out": len(out)})
    return out
