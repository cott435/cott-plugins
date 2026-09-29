"""The Trade record — the repo contract's Trades shape, one element."""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class Trade:
    """One trade from the export."""

    ts: datetime
    symbol: str
    price: float
    size: int
    side: Literal["buy", "sell"]
