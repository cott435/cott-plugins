"""Intent tests for `load_trades` — Design §5, one per stated behavior."""

from __future__ import annotations

from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from pathlib import Path

import pytest

from data.ingest import IngestError, load_trades


def test_rows_in_file_order_without_the_repeat(
    csv_path: Path, normalise: Callable[[str], str]
) -> None:
    """Design §4 steps 4–5: file order, and the row repeated under another spelling is gone."""
    rows = load_trades(csv_path, normalise=normalise)
    assert [t.symbol for t in rows] == ["AAA", "BBB", "AAA", "CCC"]
    assert (rows[1].price, rows[1].size, rows[1].side) == (20.5, 50, "sell")


def test_the_dedupe_key_takes_the_rule_it_is_handed(csv_path: Path) -> None:
    """Design §4 step 4: the key is `normalise(symbol)`; with another rule nothing repeats."""
    rows = load_trades(csv_path, normalise=lambda raw: raw)
    assert len(rows) == 5


def test_the_kept_row_keeps_its_symbol_as_read(
    make_csv: Callable[[str, list[str]], Path], normalise: Callable[[str], str]
) -> None:
    """Design §4 step 4: the first row of a key is kept, its symbol left as read."""
    p = make_csv(
        "spelt.csv",
        [
            "ts,symbol,price,size,side",
            "2026-09-01T09:00:00Z, aaa,10.0,100,buy",
            "2026-09-01T09:00:00Z,AAA,10.0,100,buy",
        ],
    )
    rows = load_trades(p, normalise=normalise)
    assert [t.symbol for t in rows] == [" aaa"]


def test_z_suffix_and_naive_timestamps_are_utc(
    csv_path: Path, normalise: Callable[[str], str]
) -> None:
    """Design §4 step 3: `Z` is accepted; a naive value is taken as UTC (D1)."""
    rows = load_trades(csv_path, normalise=normalise)
    assert rows[0].ts == datetime(2026, 9, 1, 9, 0, tzinfo=timezone.utc)
    assert rows[2].ts == datetime(2026, 9, 1, 8, 30, tzinfo=timezone.utc)
    assert all(t.ts.utcoffset() == timedelta(0) for t in rows)


def test_header_only_returns_empty(
    make_csv: Callable[[str, list[str]], Path], normalise: Callable[[str], str]
) -> None:
    """Design §5 load_trades: a file with a header and no records returns []."""
    p = make_csv("empty.csv", ["ts,symbol,price,size,side"])
    assert load_trades(p, normalise=normalise) == []


def test_missing_column_names_the_file(
    make_csv: Callable[[str, list[str]], Path], normalise: Callable[[str], str]
) -> None:
    """Design §4 step 2: a missing column raises IngestError naming the file."""
    p = make_csv(
        "short.csv", ["ts,symbol,price,size", "2026-09-01T09:00:00Z,AAA,10.0,100"]
    )
    with pytest.raises(IngestError, match=r"short\.csv: missing columns"):
        load_trades(p, normalise=normalise)


def test_bad_cell_names_file_and_line(
    make_csv: Callable[[str, list[str]], Path], normalise: Callable[[str], str]
) -> None:
    """Design §4 step 3: a cell that does not parse raises IngestError naming <file>:<line>."""
    p = make_csv(
        "bad.csv",
        [
            "ts,symbol,price,size,side",
            "2026-09-01T09:00:00Z,AAA,10.0,100,buy",
            "2026-09-01T09:05:00Z,AAA,ten,100,buy",
        ],
    )
    with pytest.raises(IngestError, match=r"bad\.csv:3: "):
        load_trades(p, normalise=normalise)


def test_missing_file_is_an_ingest_error(
    tmp_path: Path, normalise: Callable[[str], str]
) -> None:
    """Design §4 step 1: a file that cannot be opened raises IngestError naming it."""
    with pytest.raises(IngestError, match=r"nowhere\.csv: cannot be read"):
        load_trades(tmp_path / "nowhere.csv", normalise=normalise)
