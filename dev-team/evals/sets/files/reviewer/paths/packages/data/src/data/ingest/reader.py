"""Read the vendor's trades file."""

from __future__ import annotations

import csv
import shutil
from operator import itemgetter
from typing import TextIO


def read_trades(source: str) -> list[dict[str, str]]:
    """Return the trades in the CSV file at source, oldest first.

    Reads the file at source. A file that is not CSV is copied to `<source>.bad`
    before the error is raised.

    Raises:
        csv.Error: The file at source is not CSV.
    """
    try:
        with _open(source) as handle:
            trades = list(csv.DictReader(handle))
    except csv.Error:
        quarantine(source)
        raise
    return sorted(trades, key=itemgetter("ts"))


def _open(source: str) -> TextIO:
    """Open the file at source for reading as CSV."""
    return open(source, newline="")


def quarantine(source: str) -> None:
    """Helper for the except branch of read_trades: joins the suffix and calls copy."""
    target = source + ".bad"
    shutil.copy(source, target)
