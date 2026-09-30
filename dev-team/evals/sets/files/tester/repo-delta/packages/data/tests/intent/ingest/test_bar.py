"""Intent tests for the Bar row type."""

import dataclasses
from datetime import UTC, datetime
from typing import Any, cast

import pytest


def _bar():
    from data.ingest.models import Bar

    return Bar(
        "AAPL",
        datetime(2024, 3, 4, 5, tzinfo=UTC),
        176.15,
        176.9,
        173.79,
        175.1,
        81510101,
    )


def test_bar_is_frozen():
    """Design §5 Bar: assigning close raises FrozenInstanceError."""
    bar = _bar()
    with pytest.raises(dataclasses.FrozenInstanceError):
        cast(Any, bar).close = 1.0


def test_bar_field_order():
    """Design §3 Bar: fields are symbol, ts, open, high, low, close, volume in that order."""
    from data.ingest.models import Bar

    names = [f.name for f in dataclasses.fields(Bar)]
    assert names == ["symbol", "ts", "open", "high", "low", "close", "volume"]
