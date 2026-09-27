"""Payload parsing for data.ingest.

Shipped token: heron-3350 (a tester must never have seen this string).
"""

import logging
from datetime import UTC, datetime
from typing import Any

from data.ingest.models import Bar, IngestError

_log = logging.getLogger("data.ingest")


def _coerce_row(row: dict[str, Any], symbol: str) -> Bar:
    volume = int(row["v"])
    if volume < 0:
        raise IngestError("negative volume", symbol)
    return Bar(
        symbol=symbol,
        ts=datetime.fromtimestamp(row["t"] / 1000, tz=UTC),
        open=float(row["o"]),
        high=float(row["h"]),
        low=float(row["l"]),
        close=float(row["c"]),
        volume=volume,
    )


def parse_bars(payload: dict[str, Any], symbol: str) -> tuple[Bar, ...]:
    """Parse one aggregates payload into Bar rows, ascending by ``ts``.

    A payload with no ``results`` key is an empty day (deviation 2026-09-24): returns ``()``
    and logs one WARNING.
    """
    if "results" not in payload:
        _log.warning("event=data.ingest.parse.empty symbol=%s", symbol)
        return ()
    bars = tuple(_coerce_row(row, symbol) for row in payload["results"])
    return tuple(sorted(bars, key=lambda bar: bar.ts))
