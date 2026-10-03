"""Read a trades CSV into `Trade` rows.

Columns: ts (ISO 8601, UTC), symbol, price, size, side. Rows come back in file order;
nothing is deduplicated or sorted here — that is `data/clean`'s job.
"""

from __future__ import annotations

import csv
import logging
from collections.abc import Callable
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("data.ingest")

COLUMNS = ("ts", "symbol", "price", "size", "side")


class IngestError(ValueError):
    """The CSV cannot be read, is missing a column, or holds a cell that does not parse."""


@dataclass(slots=True)
class Trade:
    """One trade as read from the file; `ts` is timezone-aware UTC."""

    ts: datetime
    symbol: str
    price: float
    size: int
    side: str


def _parse_ts(raw: str) -> datetime:
    """Parse an ISO 8601 timestamp; a naive value is taken as UTC."""
    ts = datetime.fromisoformat(raw.replace("Z", "+00:00"))
    if ts.tzinfo is None:
        ts = ts.replace(tzinfo=timezone.utc)
    return ts


def _guarded(step: Callable[[], list[Trade]], *, source: Path) -> list[Trade]:
    """Run `step` and return its rows; an `OSError` becomes an `IngestError` naming `source`.

    Logs one `WARNING` line `unreadable` with `path` before raising.
    """
    try:
        rows = step()
    except OSError as exc:
        log.warning("unreadable", extra={"path": str(source)})
        raise IngestError(f"{source.name}: cannot be read") from exc
    return rows


def _read_rows(path: Path) -> list[Trade]:
    """Open `path` and parse every record of it into a `Trade`, in file order.

    Raises:
        OSError: the file cannot be opened.
        IngestError: a column is missing, or a cell does not parse.
    """
    with open(path, newline="", encoding="utf-8") as fh:
        reader = csv.DictReader(fh)
        missing = set(COLUMNS) - set(reader.fieldnames or ())
        if missing:
            raise IngestError(f"{path.name}: missing columns {sorted(missing)}")
        rows: list[Trade] = []
        for n, rec in enumerate(reader, start=2):
            try:
                rows.append(
                    Trade(
                        ts=_parse_ts(rec["ts"]),
                        symbol=rec["symbol"],
                        price=float(rec["price"]),
                        size=int(rec["size"]),
                        side=rec["side"],
                    )
                )
            except (KeyError, ValueError) as exc:
                raise IngestError(f"{path.name}:{n}: {exc}") from exc
    return rows


def load_trades(path: Path) -> list[Trade]:
    """Read every row of the CSV at `path` into a `Trade`.

    Opens and reads the file; logs one `INFO` line `loaded` with `path` and `rows_out`.

    Args:
        path: a CSV with the columns in `COLUMNS`, in any order.

    Returns:
        The rows in file order.

    Raises:
        IngestError: the file cannot be read, a column is missing, or a cell does not parse.
    """
    rows = _guarded(lambda: _read_rows(path), source=path)
    log.info("loaded", extra={"path": str(path), "rows_out": len(rows)})
    return rows
