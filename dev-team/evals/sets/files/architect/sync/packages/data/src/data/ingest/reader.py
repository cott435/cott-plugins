"""Read data/trades.csv into Trade records, stopping on the first bad row."""

from __future__ import annotations

import csv
import logging
from datetime import datetime, timezone
from pathlib import Path

from data.errors import TradeParseError
from data.ingest.model import Trade

log = logging.getLogger(__name__)

FIELDS = ("ts", "symbol", "price", "size", "side")
SIDES = ("buy", "sell")
SIDE_ALIASES = {"b": "buy", "s": "sell", "buy": "buy", "sell": "sell"}


def read_export(path: Path) -> list[Trade]:
    """Return every row of the export as a Trade, in file order.

    Raises TradeParseError on the first row with a missing or unparseable field. Row
    numbers are 1-based and count the header line as row 1.
    """
    trades: list[Trade] = []
    with path.open(newline="") as handle:
        for number, raw in enumerate(csv.DictReader(handle), start=2):
            trades.append(_parse_row(number, raw))
    log.info("read %d trades from %s", len(trades), path)
    return trades


def _parse_row(number: int, raw: dict[str, str]) -> Trade:
    for field in FIELDS:
        if not raw.get(field):
            raise TradeParseError(number, field, "is missing")
    ts = _parse_ts(number, raw["ts"])
    try:
        price = float(raw["price"])
        size = int(raw["size"])
    except ValueError as exc:
        field = "price" if "price" in str(exc) or not _is_float(raw["price"]) else "size"
        raise TradeParseError(number, field, f"is not a number: {raw[field]!r}") from exc
    if price <= 0:
        raise TradeParseError(number, "price", "must be > 0")
    if size <= 0:
        raise TradeParseError(number, "size", "must be > 0")
    side = SIDE_ALIASES.get(raw["side"].strip().lower())
    if side is None:
        raise TradeParseError(number, "side", f"must be buy, sell, B or S, got {raw['side']!r}")
    return Trade(ts=ts, symbol=raw["symbol"].upper(), price=price, size=size, side=side)  # type: ignore[arg-type]


def _parse_ts(number: int, text: str) -> datetime:
    try:
        parsed = datetime.fromisoformat(text.replace("Z", "+00:00"))
    except ValueError as exc:
        raise TradeParseError(number, "ts", f"is not ISO 8601: {text!r}") from exc
    if parsed.tzinfo is None:
        raise TradeParseError(number, "ts", "has no timezone")
    return parsed.astimezone(timezone.utc)


def _is_float(text: str) -> bool:
    try:
        float(text)
    except ValueError:
        return False
    return True
