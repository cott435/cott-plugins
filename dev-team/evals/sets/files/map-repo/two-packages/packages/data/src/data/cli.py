"""The `data-daily` command: one run date through ingest, clean and store."""

import argparse
from datetime import date
from pathlib import Path

from data.clean.rules import clean_bars
from data.ingest.loader import load_bars
from data.store.parquet import write_bars


def daily_pipeline(run_date: date, symbols: list[str], landing_dir: Path) -> list[Path]:
    """Download, clean and write one parquet file per symbol for `run_date`."""
    written: list[Path] = []
    for symbol in symbols:
        raw = load_bars(symbol, run_date, run_date)
        written.append(write_bars(clean_bars(raw), landing_dir, symbol, run_date))
    return written


def daily() -> None:
    parser = argparse.ArgumentParser(prog="data-daily")
    parser.add_argument("--run-date", type=date.fromisoformat, default=date.today())
    parser.add_argument("--symbols", nargs="+", default=["SPY"])
    parser.add_argument("--landing-dir", type=Path, default=Path("./landing"))
    args = parser.parse_args()
    for path in daily_pipeline(args.run_date, args.symbols, args.landing_dir):
        print(path)
