"""Intent tests for `Trade` — Design §5."""

from __future__ import annotations

import dataclasses
from pathlib import Path

import pytest

from data.ingest import Trade, load_export


def test_trade_is_frozen(export_path: Path) -> None:
    """Design §5 Trade: a frozen dataclass — a row cannot be changed after it is read."""
    row = load_export(export_path)[0]
    assert isinstance(row, Trade)
    with pytest.raises(dataclasses.FrozenInstanceError):
        row.price = 0.0  # type: ignore[misc]
