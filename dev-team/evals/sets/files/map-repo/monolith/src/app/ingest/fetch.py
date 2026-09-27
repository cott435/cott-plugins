"""Read one vendor CSV export into rows."""

import csv
from dataclasses import dataclass
from pathlib import Path

from app.settings import Settings


@dataclass(frozen=True)
class Row:
    account: str
    amount: str
    posted: str


def export_path(name: str, settings: Settings | None = None) -> Path:
    return (settings or Settings()).export_dir / f"{name}.csv"


def fetch_rows(path: Path) -> list[Row]:
    """Every row of the export, untyped: the vendor's strings as they are."""
    with path.open(newline="") as handle:
        return [Row(r["account"], r["amount"], r["posted"]) for r in csv.DictReader(handle)]
