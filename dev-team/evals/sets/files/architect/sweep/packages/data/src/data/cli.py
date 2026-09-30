"""data-ingest: read an export, clean it, store it."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data.clean import clean_trades
from data.errors import TradeParseError
from data.ingest import read_export
from data.storage import store_trades


def ingest(argv: list[str] | None = None) -> int:
    """The ingest pipeline: read_export → clean_trades → store_trades."""
    parser = argparse.ArgumentParser(prog="data-ingest")
    parser.add_argument("csv", type=Path)
    parser.add_argument("--db", type=Path, default=Path("./trades.sqlite"))
    args = parser.parse_args(argv)
    try:
        trades = clean_trades(read_export(args.csv))
    except TradeParseError as exc:
        print(str(exc), file=sys.stderr)
        return 1
    print(f"stored {store_trades(trades, args.db)} new rows")
    return 0
