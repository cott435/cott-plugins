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


def test_values_are_stripped_and_not_range_checked(tmp_path: Path) -> None:
    path = _export(tmp_path, "2026-09-01T13:30:20Z, aaa ,-1.5,0,buy")
    assert read_trades(path) == [
        Trade(datetime(2026, 9, 1, 13, 30, 20, tzinfo=UTC), "aaa", -1.5, 0, "buy")
    ]


def test_header_only_export_is_empty(tmp_path: Path) -> None:
    assert read_trades(_export(tmp_path)) == []


@pytest.mark.parametrize(
    ("row", "field"),
    [
        ("2026-09-01 13:30:20,AAA,49.74,280,sell", "ts"),
        ("2026-09-01T13:30:20Z,AAA,abc,280,sell", "price"),
        ("2026-09-01T13:30:20Z,AAA,49.74,2.5,sell", "size"),
        ("2026-09-01T13:30:20Z,AAA,49.74,280,hold", "side"),
        ("2026-09-01T13:30:20Z,,49.74,280,sell", "symbol"),
        ("2026-09-01T13:30:20Z,AAA,49.74,280", "side"),
    ],
)
def test_each_field_is_rejected_by_name(tmp_path: Path, row: str, field: str) -> None:
    with pytest.raises(IngestError) as caught:
        read_trades(_export(tmp_path, row))
    assert caught.value.field == field
    assert caught.value.row == 1
    assert isinstance(caught.value, DataError)
