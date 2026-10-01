"""Unit tests for the surface section: `daily` and the lazy public names."""

from datetime import date

import pandas as pd

import data
from data.pipelines import daily

START = date(2026, 3, 5)
END = date(2026, 3, 6)


def _fetch(symbol: str, start: date, end: date) -> pd.DataFrame:
    rows = [
        (symbol, "2026-03-05", 1.0, 1.0, 1.0, 1.0, 5),
        (symbol, "2026-03-06", 1.0, 1.0, 1.0, 2.0, 5),
    ]
    columns = ["symbol", "timestamp", "open", "high", "low", "close", "volume"]
    frame = pd.DataFrame(rows, columns=columns)
    frame["timestamp"] = pd.to_datetime(frame["timestamp"])
    return frame


def test_daily_creates_the_run_folder(tmp_path):
    landing = tmp_path / "landing"
    daily(["AAA"], START, END, landing, _fetch)
    assert (landing / "2026-03-06").is_dir()


def test_daily_returns_paths_in_symbol_order(tmp_path):
    written = daily(["BBB", "AAA"], START, END, tmp_path, _fetch)
    assert [path.stem for path in written] == ["BBB", "AAA"]


def test_getattr_caches_the_imported_name():
    first = data.clean_bars
    assert vars(data)["clean_bars"] is first
