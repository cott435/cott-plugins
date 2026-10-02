"""Unit tests for `data.ingest.loader`."""

from __future__ import annotations

import logging
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from data.ingest.loader import (
    IngestError,
    Trade,
    _drop_repeats,
    _parse_ts,
    load_trades,
)

_AT = datetime(2026, 9, 1, 9, tzinfo=timezone.utc)


def test_parse_ts_takes_a_naive_value_as_utc() -> None:
    """A timestamp with no offset is labelled UTC, not shifted."""
    assert _parse_ts("2026-09-01T09:00:00") == _AT


def test_parse_ts_accepts_z() -> None:
    """The venue's trailing `Z` parses as UTC."""
    assert _parse_ts("2026-09-01T09:00:00Z").utcoffset() == timedelta(0)


def test_parse_ts_keeps_an_offset() -> None:
    """An aware value keeps its own offset."""
    assert _parse_ts("2026-09-01T09:00:00+02:00").utcoffset() == timedelta(hours=2)


def test_drop_repeats_keeps_the_first_spelling() -> None:
    """Two rows whose symbols differ only in spelling are one trade; the first stays."""
    rows = [Trade(_AT, "aaa ", 10.0, 100, "buy"), Trade(_AT, "AAA", 10.0, 100, "buy")]
    out = _drop_repeats(rows, lambda raw: raw.strip().upper())
    assert [t.symbol for t in out] == ["aaa "]


def test_missing_file_logs_unreadable(
    tmp_path: Path, caplog: pytest.LogCaptureFixture
) -> None:
    """An unreadable file logs one WARNING `unreadable` with its path, then raises."""
    missing = tmp_path / "nowhere.csv"
    with (
        caplog.at_level(logging.WARNING, logger="data.ingest"),
        pytest.raises(IngestError),
    ):
        load_trades(missing, normalise=str.upper)
    lines = [r for r in caplog.records if r.msg == "unreadable"]
    assert len(lines) == 1
    assert lines[0].path == str(missing)
