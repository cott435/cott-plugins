"""Intent tests for `Bar` — Design §3 and §5."""

from __future__ import annotations

import dataclasses
from datetime import datetime, timezone

import pytest

from data.bars import Bar


def test_bar_fields_in_order() -> None:
    """Design §3: the ten fields of the Bar shape, in the order given."""
    assert [f.name for f in dataclasses.fields(Bar)] == [
        "symbol",
        "start",
        "open",
        "high",
        "low",
        "close",
        "vwap",
        "volume",
        "buy_volume",
        "trades",
    ]


def test_bar_is_frozen() -> None:
    """Design §3: `Bar` is a frozen dataclass."""
    bar = Bar(
        "AAA",
        datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc),
        1.0,
        1.0,
        1.0,
        1.0,
        1.0,
        1,
        1,
        1,
    )
    with pytest.raises(dataclasses.FrozenInstanceError):
        bar.close = 2.0  # type: ignore[misc]
