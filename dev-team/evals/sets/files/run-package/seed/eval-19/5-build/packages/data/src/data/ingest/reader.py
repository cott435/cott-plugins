"""Read the analyst's CSV export into `Trade` records, in file order."""

import csv
from collections.abc import Mapping
from datetime import UTC, datetime
from pathlib import Path
from typing import Literal

from data.ingest.errors import IngestError
from data.ingest.models import Trade

_TS_FORMAT = "%Y-%m-%dT%H:%M:%SZ"


def read_trades(path: Path) -> list[Trade]:
    """Read every data row of the export, in file order, duplicates included.

    Args:
        path: The CSV export: one header line, then one trade per line.

    Returns:
        One `Trade` per data row.

    Raises:
        IngestError: On the first row with a missing or unparseable field.
    """
    with path.open(newline="", encoding="utf-8") as handle:
        return [
            _parse_row(number, row)
            for number, row in enumerate(csv.DictReader(handle), start=1)
        ]


def _parse_row(number: int, row: Mapping[str, str | None]) -> Trade:
    """Turn one CSV row into a `Trade`, or raise naming the row and the field."""
    return Trade(
        ts=_parse_ts(number, _value(number, row, "ts")),
        symbol=_value(number, row, "symbol"),
        price=_parse_price(number, _value(number, row, "price")),
        size=_parse_size(number, _value(number, row, "size")),
        side=_parse_side(number, _value(number, row, "side")),
    )


def _value(number: int, row: Mapping[str, str | None], field: str) -> str:
    """The row's value for a column, rejected when absent or empty."""
    value = row.get(field)
    if value is None or not value.strip():
        raise IngestError(number, field, "missing")
    return value.strip()


def _parse_ts(number: int, value: str) -> datetime:
    """An ISO 8601 `Z` timestamp as a tz-aware UTC datetime."""
    try:
        return datetime.strptime(value, _TS_FORMAT).replace(tzinfo=UTC)
    except ValueError as error:
        reason = f"not an ISO 8601 UTC timestamp: {value!r}"
        raise IngestError(number, "ts", reason) from error


def _parse_price(number: int, value: str) -> float:
    """A price as a float."""
    try:
        return float(value)
    except ValueError as error:
        raise IngestError(number, "price", f"not a number: {value!r}") from error


def _parse_size(number: int, value: str) -> int:
    """A size as an int."""
    try:
        return int(value)
    except ValueError as error:
        raise IngestError(number, "size", f"not an integer: {value!r}") from error


def _parse_side(number: int, value: str) -> Literal["buy", "sell"]:
    """A side, one of `buy` and `sell`."""
    if value == "buy":
        return "buy"
    if value == "sell":
        return "sell"
    raise IngestError(number, "side", f"not 'buy' or 'sell': {value!r}")
