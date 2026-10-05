"""The `Trade` shape of `docs/architecture.md`."""

from dataclasses import dataclass
from datetime import datetime
from typing import Literal


@dataclass(frozen=True)
class Trade:
    """One trade of the analyst's export.

    Attributes:
        ts: When the trade happened, tz-aware UTC.
        symbol: The instrument, as the export spells it.
        price: The trade price.
        size: The number of units traded.
        side: `"buy"` or `"sell"`.
    """

    ts: datetime
    symbol: str
    price: float
    size: int
    side: Literal["buy", "sell"]
