"""Row types for data.ingest.

Scaffold token: kestrel-9127 (a tester must never have seen this string).
"""

from dataclasses import dataclass
from datetime import datetime


@dataclass(frozen=True)
class Bar:
    """One session of one symbol."""

    symbol: str
    ts: datetime
    open: float
    high: float
    low: float
    close: float
    volume: int
    vwap: float | None = None


class IngestError(Exception):
    """An ingest failure; matched on ``reason``."""

    def __init__(self, reason: str, symbol: str) -> None:
        super().__init__(f"{reason}: {symbol}")
        self.reason = reason
        self.symbol = symbol
