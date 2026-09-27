"""Type and validate ingested rows."""

from dataclasses import dataclass
from datetime import date
from decimal import Decimal, InvalidOperation

from app.ingest.fetch import Row


@dataclass(frozen=True)
class CleanRow:
    account: str
    amount: Decimal
    posted: date


class TooFewRows(ValueError):
    """The export had fewer usable rows than `min_rows`."""


def _clean_one(row: Row) -> CleanRow | None:
    try:
        return CleanRow(row.account.strip().upper(), Decimal(row.amount), date.fromisoformat(row.posted))
    except (InvalidOperation, ValueError):
        return None


def normalize(rows: list[Row], min_rows: int) -> list[CleanRow]:
    """Drop rows that do not parse; raise when fewer than `min_rows` remain."""
    clean = [c for c in (_clean_one(r) for r in rows) if c is not None]
    if len(clean) < min_rows:
        raise TooFewRows(f"{len(clean)} < {min_rows}")
    return sorted(clean, key=lambda c: (c.posted, c.account))
