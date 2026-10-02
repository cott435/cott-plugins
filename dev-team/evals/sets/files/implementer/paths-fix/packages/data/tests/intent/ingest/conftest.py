"""Fixtures for the `data/ingest` intent tests, built from the documents only.

One valid CSV: the header and four records, the third with a naive timestamp, the columns
not in the order the design lists them.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

CSV = [
    "symbol,ts,side,price,size",
    "AAA,2026-09-01T09:00:00Z,buy,10.0,100",
    "BBB,2026-09-01T10:00:00+00:00,sell,20.5,50",
    "AAA,2026-09-01T08:30:00,sell,10.5,10",
    "CCC,2026-09-01T07:00:00Z,buy,5.25,200",
]


@pytest.fixture
def make_csv(tmp_path: Path) -> Callable[[str, list[str]], Path]:
    """Write `lines` as a CSV named `name` under `tmp_path`; return its path."""

    def write(name: str, lines: list[str]) -> Path:
        p = tmp_path / name
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p

    return write


@pytest.fixture
def csv_path(make_csv: Callable[[str, list[str]], Path]) -> Path:
    """The valid CSV above."""
    return make_csv("trades.csv", CSV)
