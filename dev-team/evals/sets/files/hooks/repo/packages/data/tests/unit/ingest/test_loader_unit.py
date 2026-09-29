"""Unit tests for data/ingest, below the intent suite: the loader's field list."""

from data.ingest.loader import FIELDS


def test_fields_are_the_export_header() -> None:
    assert FIELDS == ("ts", "symbol", "price", "size", "side")
