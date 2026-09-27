"""Intent tests for data/ingest, written from the design and the contracts."""

from pathlib import Path

import pytest

from data.errors import TradeParseError
from data.ingest import read_export

FIXTURE = Path(__file__).resolve().parents[4] / "data" / "trades.csv"


def test_reads_every_row():
    """Design §7 read_export: the fixture yields 400 records in file order."""
    assert len(read_export(FIXTURE)) == 400


def test_bad_side_names_the_field(tmp_path: Path):
    """Design §6 TradeParseError: a side other than buy/sell names row and field."""
    csv = tmp_path / "t.csv"
    csv.write_text("ts,symbol,price,size,side\n2026-09-01T13:30:20Z,AAA,1.0,1,hold\n")
    with pytest.raises(TradeParseError) as info:
        read_export(csv)
    assert info.value.row == 2 and info.value.field == "side"
