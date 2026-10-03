"""The `load` pipeline: the vendor's trades file into the trades database."""

from __future__ import annotations

from collections.abc import Callable

from loguru import logger

from data.ingest.reader import read_trades
from data.store.writer import write_trades

Trades = list[dict[str, str]]


def guarded(step: Callable[[], Trades]) -> Trades:
    """Run step and return its result, logging `data.load.failed` when it raises."""
    try:
        return step()
    except Exception:
        logger.exception("data.load.failed")
        raise


def run_load(source: str, target: str) -> int:
    """Load the trades in the CSV at source into the SQLite database at target.

    Returns:
        The number of trades inserted.
    """
    trades = guarded(lambda: read_trades(source))
    return write_trades(target, trades)
