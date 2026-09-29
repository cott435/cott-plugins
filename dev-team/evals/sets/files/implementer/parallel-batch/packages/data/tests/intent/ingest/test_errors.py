"""Intent tests for `IngestError` — Design §5 error cases."""

from __future__ import annotations

from collections.abc import Callable
from pathlib import Path

import pytest

from data.ingest import IngestError, load_export


def test_unknown_side_code_names_file_and_line(
    make_export: Callable[[str, list[str]], Path],
) -> None:
    """Design §5 load_export: an unknown side code raises IngestError naming <file>:<line>."""
    p = make_export(
        "bad-side.csv",
        [
            "# venue=XVEN",
            "TradeTime;Ticker;Px;Qty;Side",
            "29.09.2026 09:00:00 +02:00;ABC;10.5;100;B",
            "29.09.2026 09:00:01 +02:00;ABC;10.5;100;X",
        ],
    )
    with pytest.raises(IngestError, match=r"bad-side\.csv:4\b"):
        load_export(p)
    assert issubclass(IngestError, ValueError)


def test_missing_column_names_file_and_header_line(
    make_export: Callable[[str, list[str]], Path],
) -> None:
    """Design §5 load_export: a missing column raises IngestError naming the header's line."""
    p = make_export(
        "no-side.csv",
        [
            "# venue=XVEN",
            "# exported=2026-09-29T18:00:00+02:00",
            "TradeTime;Ticker;Px;Qty",
            "29.09.2026 09:00:00 +02:00;ABC;10.5;100",
        ],
    )
    with pytest.raises(IngestError, match=r"no-side\.csv:3\b"):
        load_export(p)
