"""Read a trades CSV into `Trade` rows and drop the rows the export repeats.

Columns: ts (ISO 8601, UTC), symbol, price, size, side. Rows come back in file order with
their symbols as read; rewriting symbols and sorting are `data/clean`'s job.
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

Key = tuple[datetime, str, float, int, str]


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


def _drop_repeats(rows: list[Trade], normalise: Callable[[str], str]) -> list[Trade]:
    """Return `rows` without the rows the export repeats, the first of each kept.

    Two rows repeat each other when their fields are equal once `normalise` has been
    applied to `symbol`. The kept row's own `symbol` is left as read.
    """
    seen: set[Key] = set()
    out: list[Trade] = []
    for row in rows:
        key = (row.ts, normalise(row.symbol), row.price, row.size, row.side)
        if key not in seen:
            seen.add(key)
            out.append(row)
    return out


def load_trades(path: Path, *, normalise: Callable[[str], str]) -> list[Trade]:
    """Read the CSV at `path` into `Trade` rows, without the rows the export repeats.

    Opens and reads the file; logs one `INFO` line `loaded` with `path`, `rows_out` and
    `dropped`, or one `WARNING` line `unreadable` before raising for a file it cannot open.

    Args:
        path: a CSV with the columns in `COLUMNS`, in any order.
        normalise: the canonical form of a symbol, used for the dedupe key only; the
            `daily` pipeline passes `clean.normalise_symbol`.

    Returns:
        The rows in file order, the first of each set of repeats kept, symbols as read.

    Raises:
        IngestError: the file cannot be read, a column is missing, or a cell does not parse.
    """
    # 1. read the file into rows, in file order
    try:
        rows = _read_rows(path)
    except OSError as exc:
        log.warning("unreadable", extra={"path": str(path)})
        raise IngestError(f"{path.name}: cannot be read") from exc
    # 2. dedupe: drop the rows the export repeats
    unique = _drop_repeats(rows, normalise)
    log.info(
        "loaded",
        extra={
            "path": str(path),
            "rows_out": len(unique),
            "dropped": len(rows) - len(unique),
        },
    )
    return unique
