"""The `load` pipeline: the vendor's trades file into the trades database."""

from __future__ import annotations

from data.ingest.reader import read_trades
from data.store.writer import write_trades


def run_load(source: str, target: str) -> int:
    """Load the trades in the CSV at source into the SQLite database at target.

    Reads the file at source with `read_trades` and inserts its trades into the
    `trades` table of the database at target with `write_trades`.

    Returns:
        The number of trades inserted.
    """
    # Read the vendor's file into trades, oldest first.
    trades = read_trades(source)
    # Insert them into the trades table, in one transaction.
    inserted = write_trades(target, trades=trades)
    return inserted
