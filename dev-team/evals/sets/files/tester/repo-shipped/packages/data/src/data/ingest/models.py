"""Row types for data.ingest."""

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


class IngestError(Exception):
    """An ingest failure; callers match on ``reason``."""

    def __init__(self, reason: str, symbol: str) -> None:
        super().__init__(f"{reason}: {symbol}")
        self.reason = reason
        self.symbol = symbol
