"""Unit tests for data/ingest/reader.py."""

from data.ingest.reader import _is_float


def test_is_float():
    assert _is_float("1.5") and not _is_float("x")
