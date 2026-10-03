"""The `daily` pipeline: a trades CSV in, a TradeTable out."""

from __future__ import annotations

from pathlib import Path

from data.clean import clean_trades
from data.ingest import Trade, load_trades


def daily(csv: Path) -> list[Trade]:
    """Read the trades in `csv` and return them as a TradeTable; writes nothing.

    Args:
        csv: the venue's export for one day.

    Returns:
        The file's trades with exact duplicates collapsed, sorted by `ts` then `symbol`.

    Raises:
        IngestError: the file cannot be read, lacks a column, or holds a bad cell.
    """
    # 1. read the export into Trade rows, in file order
    rows = load_trades(csv)
    # 2. collapse exact duplicates and sort by (ts, symbol)
    return clean_trades(rows)
