"""The `verify` pipeline: every vendor file in a drop directory checked for the header."""

from __future__ import annotations

import csv
import os
from collections.abc import Callable

from data.ingest.checks import check_header

RETRIES = 2


def run_verify(source_dir: str) -> list[str]:
    """Return the vendor files under source_dir that do not carry the vendor header.

    Checks every file under source_dir with `check_header`, re-reading a file that is not
    yet CSV while the vendor may still be writing it.

    Returns:
        The paths that failed, in name order; empty when every file passed.
    """
    results = _each_source(source_dir, lambda path: _verify_one(path))
    return [path for path, ok in results if not ok]


def _each_source(source_dir: str, step: Callable[[str], bool]) -> list[tuple[str, bool]]:
    """Run step on every file under source_dir, in name order, and pair each path with its result."""
    return [
        (os.path.join(source_dir, name), step(os.path.join(source_dir, name)))
        for name in sorted(os.listdir(source_dir))
    ]


def _verify_one(path: str) -> bool:
    """Check one file, re-reading it while the vendor may still be writing it."""
    return _attempt(path, RETRIES)


def _attempt(path: str, retries: int) -> bool:
    """Check the header of the file at path, retrying a read that fails as CSV."""
    for remaining in range(retries, -1, -1):
        try:
            return check_header(path)
        except csv.Error:
            if remaining == 0:
                return False
    return False
