"""The package's pipelines: `daily`, and `main`, the `data-daily` command."""

from __future__ import annotations

import argparse
import logging
import os
from collections.abc import Callable, Sequence
from datetime import date
from pathlib import Path

import pandas as pd

from data.clean.api import clean_bars
from data.clean.errors import EmptyBars
from data.ingest.client import fetch_bars
from data.ingest.errors import VendorUnavailable

log = logging.getLogger("data.daily")

Fetch = Callable[[str, date, date], pd.DataFrame]


def daily(
    symbols: Sequence[str],
    start: date,
    end: date,
    landing_dir: Path,
    fetch: Fetch = fetch_bars,
) -> list[Path]:
    """Fetch, clean and land each symbol's bars for `start` to `end`.

    Args:
        symbols: The symbols to pull, in order.
        start: First day of the range.
        end: Last day of the range, and the run date the files land under.
        landing_dir: The directory the run's folder is created in.
        fetch: What pulls one symbol's bars; `fetch_bars` unless a caller replaces it.

    Returns:
        The parquet files written, one per symbol that had bars.

    Raises:
        VendorUnavailable: The vendor kept refusing a symbol; the run ends there.
    """
    run_dir = landing_dir / end.isoformat()
    run_dir.mkdir(parents=True, exist_ok=True)
    written: list[Path] = []
    for symbol in symbols:
        raw = fetch(symbol, start, end)
        try:
            bars = clean_bars(raw)
        except EmptyBars:
            log.info("data.daily.skipped", extra={"symbol": symbol})
            continue
        # TODO(decision D3): one file per symbol is the assumption while D3 is open.
        path = run_dir / f"{symbol}.parquet"
        bars.to_parquet(path, index=False)
        written.append(path)
    return written


def main(argv: Sequence[str] | None = None, fetch: Fetch = fetch_bars) -> int:
    """Run the `daily` pipeline from the command line.

    Args:
        argv: `SYMBOL [SYMBOL ...] --start YYYY-MM-DD --end YYYY-MM-DD`; the
            process's arguments when None.
        fetch: Passed through to `daily`.

    Returns:
        0 when the run finished, 2 when the vendor was unavailable.
    """
    parser = argparse.ArgumentParser(prog="data-daily")
    parser.add_argument("symbols", nargs="+")
    parser.add_argument("--start", type=date.fromisoformat, required=True)
    parser.add_argument("--end", type=date.fromisoformat, required=True)
    args = parser.parse_args(argv)
    landing_dir = Path(os.environ["DATA_LANDING_DIR"])
    try:
        daily(args.symbols, args.start, args.end, landing_dir, fetch)
    except VendorUnavailable as error:
        log.error("data.daily.aborted", extra={"symbol": error.symbol})
        return 2
    return 0
