"""Fixtures for the `data/ingest` intent tests, built from the documents only.

The export dialect is the project skill `venue-csv` (design §9). One valid export: two header
comments, the header row, three trades, and a `# rows=` checkpoint between the second and
third trade.
"""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

EXPORT = [
    "# venue=XVEN",
    "# exported=2026-09-29T18:00:00+02:00",
    "TradeTime;Ticker;Px;Qty;Side",
    "29.09.2026 09:00:00 +02:00;ABC;10.5;100;B",
    "29.09.2026 09:00:05 +02:00;XYZ;20.25;1'200;S",
    "# rows=2",
    "29.09.2026 09:01:00 +02:00;ABC;10.75;50;S",
]


@pytest.fixture
def make_export(tmp_path: Path) -> Callable[[str, list[str]], Path]:
    """Write `lines` as an export file named `name` under `tmp_path`; return its path."""

    def write(name: str, lines: list[str]) -> Path:
        p = tmp_path / name
        p.write_text("\n".join(lines) + "\n", encoding="utf-8")
        return p

    return write


@pytest.fixture
def export_path(make_export: Callable[[str, list[str]], Path]) -> Path:
    """The valid export above."""
    return make_export("2026-09-29.csv", EXPORT)
