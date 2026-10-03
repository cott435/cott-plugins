"""Read a trades CSV into `Trade` rows.

Columns: ts (ISO 8601, UTC), symbol, price, size, side. Rows come back in file order;
nothing is filtered, sorted or aggregated here — that is `data/bars`' job.
"""

from __future__ import annotations

import csv
import logging
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

log = logging.getLogger("data.ingest")

COLUMNS = ("ts", "symbol", "price", "size", "side")


class IngestError(ValueError):
    """The CSV is missing a column or a cell cannot be parsed."""


@dataclass(frozen=True, slots=True)
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


def load_trades(path: Path) -> list[Trade]:
    """Read every row of `path` into a `Trade`.

    Args:
        path: a CSV with the columns in `COLUMNS`, in any order.

    Returns:
        The rows in file order.

    Raises:
        IngestError: a column is missing, or a cell does not parse.
    """
    with path.open(newline="") as fh:
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
    log.info("loaded", extra={"path": str(path), "rows": len(rows)})
    return rows
