"""Rolling volume-weighted average price per symbol over the last `window` trades."""

from __future__ import annotations

from collections import deque
from dataclasses import dataclass
from datetime import datetime

from analysis.errors import AnalysisError
from data.ingest import Trade


@dataclass(frozen=True)
class VwapPoint:
    """The VWAP of one symbol's last `window` trades, as of one trade."""

    symbol: str
    ts: datetime
    vwap: float


def rolling_vwap(trades: list[Trade], window: int) -> list[VwapPoint]:
    """One point per trade, in input order; each symbol keeps its own window of trades."""
    if window < 1:
        raise AnalysisError(f"window must be >= 1, got {window}")
    windows: dict[str, deque[Trade]] = {}
    points: list[VwapPoint] = []
    for trade in trades:
        recent = windows.setdefault(trade.symbol, deque(maxlen=window))
        recent.append(trade)
        notional = sum(t.price * t.size for t in recent)
        volume = sum(t.size for t in recent)
        points.append(VwapPoint(symbol=trade.symbol, ts=trade.ts, vwap=notional / volume))
    return points
