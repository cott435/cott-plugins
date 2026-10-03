"""Intent tests for `Trade` and `IngestError` — Design §3 and §5."""

from __future__ import annotations

import dataclasses

from data.ingest import IngestError, Trade


def test_trade_fields_in_order() -> None:
    """Design §3: the five fields of the Trade shape."""
    assert [f.name for f in dataclasses.fields(Trade)] == [
        "ts",
        "symbol",
        "price",
        "size",
        "side",
    ]


def test_ingest_error_is_a_value_error() -> None:
    """Design §5 IngestError: a subclass of ValueError (repo contract, Shared conventions)."""
    assert issubclass(IngestError, ValueError)
