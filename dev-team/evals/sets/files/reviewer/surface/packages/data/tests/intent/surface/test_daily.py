"""Intent tests for `daily` and the `data-daily` command (design §4, §6)."""

import logging
from datetime import date

import pandas as pd
import pytest

from data.ingest.errors import VendorUnavailable
from data.pipelines import daily, main

START = date(2026, 3, 5)
END = date(2026, 3, 6)
COLUMNS = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]


def _unavailable(symbol: str, start: date, end: date) -> pd.DataFrame:
    raise VendorUnavailable(symbol)


@pytest.mark.xfail(
    reason="D3 open: assumes one parquet file per symbol, <run_date>/<symbol>.parquet",
    strict=False,
)
def test_lands_one_file_per_symbol(tmp_path, fetch):
    """Design §4 step 3: each symbol's bars land in `<run_date>/<symbol>.parquet`."""
    daily(["AAA", "BBB"], START, END, tmp_path, fetch)
    assert (tmp_path / "2026-03-06" / "AAA.parquet").is_file()
    assert (tmp_path / "2026-03-06" / "BBB.parquet").is_file()


def test_landed_file_is_a_bar_frame(tmp_path, fetch):
    """Design §4 step 3: a landed file reads back with the seven BarFrame columns."""
    written = daily(["AAA"], START, END, tmp_path, fetch)
    assert len(written) == 1
    assert list(pd.read_parquet(written[0]).columns) == COLUMNS


def test_symbol_with_no_bars_is_skipped_and_logged(tmp_path, fetch, caplog):
    """Design §6 EmptyBars from clean_bars: skipped, logged, and the others land."""
    with caplog.at_level(logging.INFO, logger="data.daily"):
        written = daily(["NONE", "AAA"], START, END, tmp_path, fetch)
    assert len(written) == 1
    skipped = [r for r in caplog.records if r.getMessage() == "data.daily.skipped"]
    assert len(skipped) == 1
    assert skipped[0].symbol == "NONE"


def test_vendor_unavailable_leaves_daily(tmp_path):
    """Design §6 VendorUnavailable from fetch: `daily` lets it propagate."""
    with pytest.raises(VendorUnavailable):
        daily(["AAA"], START, END, tmp_path, _unavailable)


def test_command_returns_2_when_vendor_unavailable(tmp_path, monkeypatch):
    """Design §6 VendorUnavailable from fetch: `main` returns 2."""
    monkeypatch.setenv("DATA_LANDING_DIR", str(tmp_path))
    argv = ["AAA", "--start", "2026-03-05", "--end", "2026-03-06"]
    assert main(argv, _unavailable) == 2


def test_command_returns_0_when_run_finished(tmp_path, monkeypatch, fetch):
    """Design §6 the run finished: `main` returns 0."""
    monkeypatch.setenv("DATA_LANDING_DIR", str(tmp_path))
    argv = ["AAA", "--start", "2026-03-05", "--end", "2026-03-06"]
    assert main(argv, fetch) == 0
