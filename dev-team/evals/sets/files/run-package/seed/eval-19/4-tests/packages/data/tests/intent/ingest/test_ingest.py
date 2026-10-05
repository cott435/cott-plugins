from datetime import UTC, datetime
from pathlib import Path

import pytest
from data.ingest.errors import DataError, IngestError
from data.ingest.models import Trade
from data.ingest.reader import read_trades

HEADER = "ts,symbol,price,size,side\n"


def _export(tmp_path: Path, *rows: str) -> Path:
    path = tmp_path / "trades.csv"
    path.write_text(HEADER + "".join(f"{row}\n" for row in rows), encoding="utf-8")
    return path


def test_rows_come_back_in_file_order_with_duplicates(tmp_path: Path) -> None:
    """Design §4 step 2, §7 case 1: file order kept, duplicates kept."""
    path = _export(
        tmp_path,
        "2026-09-01T15:14:08Z,BBB,119.98,420,sell",
        "2026-09-01T15:10:12Z,CCC,8.65,380,buy",
        "2026-09-01T15:10:12Z,CCC,8.65,380,buy",
    )
    first = Trade(
        datetime(2026, 9, 1, 15, 14, 8, tzinfo=UTC), "BBB", 119.98, 420, "sell"
    )
    second = Trade(
        datetime(2026, 9, 1, 15, 10, 12, tzinfo=UTC), "CCC", 8.65, 380, "buy"
    )
    assert read_trades(path) == [first, second, second]


def test_ts_is_timezone_aware_utc(tmp_path: Path) -> None:
    """Design §2, §7 case 2: `ts` carries UTC."""
    trade = read_trades(_export(tmp_path, "2026-09-01T13:30:20Z,AAA,49.74,280,sell"))[0]
    assert trade.ts.tzinfo is not None
    assert trade.ts.utcoffset() == UTC.utcoffset(None)


def test_unparseable_field_names_row_and_field(tmp_path: Path) -> None:
    """Design §6, §7 case 3: the first rejected row, 1-based, and its field."""
    path = _export(
        tmp_path,
        "2026-09-01T13:30:20Z,AAA,49.74,280,sell",
        "2026-09-01T13:30:41Z,CCC,eight,110,sell",
    )
    with pytest.raises(IngestError) as caught:
        read_trades(path)
    assert caught.value.row == 2
    assert caught.value.field == "price"
    assert "2" in str(caught.value)
    assert "price" in str(caught.value)
    assert caught.value.reason in str(caught.value)


def test_missing_field_is_rejected(tmp_path: Path) -> None:
    """Design §6, §7 case 4: an empty field is a rejection, a `DataError`."""
    path = _export(tmp_path, "2026-09-01T13:30:20Z,AAA,49.74,,sell")
    with pytest.raises(DataError) as caught:
        read_trades(path)
    assert isinstance(caught.value, IngestError)
    assert caught.value.field == "size"
