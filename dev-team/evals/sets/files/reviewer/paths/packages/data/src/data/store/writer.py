"""Write trades to the trades database."""

from __future__ import annotations

import sqlite3

INSERT_TRADE = "INSERT INTO trades (ts, symbol, price, size) VALUES (?, ?, ?, ?)"


def write_trades(target: str, trades: list[dict[str, str]]) -> int:
    """Insert trades into the `trades` table of the SQLite database at target.

    Opens the database at target, inserts one row per trade in one transaction and
    commits it.

    Returns:
        The number of rows inserted.
    """
    rows = _rows(trades)
    with sqlite3.connect(target) as connection:
        connection.executemany(INSERT_TRADE, rows)
    return len(rows)


def _rows(trades: list[dict[str, str]]) -> list[tuple[str, str, float, int]]:
    """Return one `(ts, symbol, price, size)` tuple per trade."""
    return [
        (trade["ts"], trade["symbol"], float(trade["price"]), int(trade["size"]))
        for trade in trades
    ]
