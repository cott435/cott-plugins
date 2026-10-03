"""Intent tests for data/ingest, written from docs/packages/data/design/ingest.md."""

from pathlib import Path

import pytest
from data.ingest import load_trades

HEADER = "ts,symbol,price,size,side\n"


def test_load_trades_returns_rows(tmp_path: Path) -> None:
    """Design §5 load_trades: one dict per CSV row, keyed by the header."""
    csv_file = tmp_path / "trades.csv"
    csv_file.write_text(HEADER + "2026-09-01T13:30:20Z,AAA,49.74,280,sell\n")
    assert load_trades(csv_file) == [
        {
            "ts": "2026-09-01T13:30:20Z",
            "symbol": "AAA",
            "price": "49.74",
            "size": "280",
            "side": "sell",
        }
    ]


def test_load_trades_rejects_missing_field(tmp_path: Path) -> None:
    """Design §6 bad row: a row with a missing field raises ValueError naming the field."""
    csv_file = tmp_path / "trades.csv"
    csv_file.write_text(HEADER + "2026-09-01T13:30:20Z,AAA,49.74,,sell\n")
    with pytest.raises(ValueError, match="size"):
        load_trades(csv_file)
