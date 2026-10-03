"""Check a vendor file's header before it is loaded."""

from __future__ import annotations

import csv
from typing import TextIO

HEADER = ["ts", "symbol", "price", "size"]


def check_header(path: str) -> bool:
    """Return whether the CSV file at path starts with the vendor header.

    Reads the file at path.

    Raises:
        csv.Error: The file at path is not CSV.
    """
    return _first_row(path) == HEADER


def _first_row(path: str) -> list[str]:
    """Return the first row of the CSV file at path, empty for an empty file."""
    rows = _rows(path)
    return rows[0] if rows else []


def _rows(path: str) -> list[list[str]]:
    """Return every row of the CSV file at path."""
    with _open(path) as handle:
        return list(csv.reader(handle))


def _open(path: str) -> TextIO:
    """Open the file at path for reading as CSV."""
    return open(path, newline="")
