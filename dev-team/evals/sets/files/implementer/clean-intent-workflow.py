"""End-to-end paths for `data/clean` — Design §4, `daily` pipeline steps 1–2, and §8."""

from __future__ import annotations

from pathlib import Path

from data.clean import clean_trades
from data.ingest import load_trades

_HEADER = "ts,symbol,price,size,side"


def _write_csv(tmp_path: Path, rows: list[str]) -> Path:
    """Write `rows` under the header row as a CSV in `tmp_path`; return its path."""
    p = tmp_path / "ties.csv"
    p.write_text("\n".join(_HEADER, *rows) + "\n")
    return p


def test_csv_through_ingest_and_clean(csv_path: Path) -> None:
    """Design §4 workflow: load_trades then clean_trades yields a sorted, deduped table."""
    table = clean_trades(load_trades(csv_path))
    assert len(table) == 6
    hours = [t.ts.hour for t in table]
    assert hours == sorted(hours)
    assert hours[0] == 7


def test_tied_rows_keep_file_order(tmp_path: Path) -> None:
    """Design §8 pitfall 1: rows tied on (ts, symbol) come out in file order."""
    p = _write_csv(
        tmp_path,
        [
            "2026-09-01T10:00:00Z,BBB,20.5,50,buy",
            "2026-09-01T10:00:00Z,BBB,20.5,50,sell",
        ],
    )
    table = clean_trades(load_trades(p))
    assert [t.side for t in table] == ["buy", "sell"]
