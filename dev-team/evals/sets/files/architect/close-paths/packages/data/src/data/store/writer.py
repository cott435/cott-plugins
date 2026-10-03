"""Write trades to the trades database."""

from __future__ import annotations

import sqlite3

INSERT_TRADE = "INSERT INTO trades (ts, symbol, price, size) VALUES (:ts, :symbol, :price, :size)"


def write_trades(target: str, trades: list[dict[str, str]]) -> int:
    """Insert trades into the `trades` table of the SQLite database at target.

    Opens the database at target, inserts one row per trade in one transaction and
    commits it.

    Returns:
        The number of rows inserted.
    """
    with sqlite3.connect(target) as connection:
        connection.executemany(INSERT_TRADE, trades)
    return len(trades)
