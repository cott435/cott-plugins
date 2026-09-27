"""Vendor calls and the retry loop for data.ingest."""

import logging
from datetime import date
from typing import Any, Protocol

from data.ingest.models import Bar, IngestError
from data.ingest.parse import parse_bars

_log = logging.getLogger("data.ingest")


class VendorError(Exception):
    """A non-2xx vendor response."""

    def __init__(self, status: int) -> None:
        super().__init__(f"vendor {status}")
        self.status = status


class VendorClient(Protocol):
    """What fetch_bars needs from a vendor client."""

    def get(self, path: str, params: dict[str, str]) -> dict[str, Any]: ...


def fetch_bars(
    symbol: str,
    start: date,
    end: date,
    *,
    client: VendorClient,
    retries: int = 3,
) -> tuple[Bar, ...]:
    """Fetch one symbol's daily bars for [start, end] and parse them."""
    if end < start:
        raise IngestError("empty range", symbol)
    path = f"/v2/aggs/ticker/{symbol}/range/1/day/{start.isoformat()}/{end.isoformat()}"
    params = {"adjusted": "true", "sort": "asc"}
    attempt = 0
    while True:
        try:
            payload = client.get(path, params)
            break
        except VendorError as exc:
            if exc.status == 429 and attempt < retries:
                attempt += 1
                continue
            raise IngestError(f"vendor {exc.status}", symbol) from exc
    bars = parse_bars(payload, symbol)
    _log.info("event=data.ingest.fetch symbol=%s bars=%d", symbol, len(bars))
    return bars
