"""Public entry point of the clean section: `clean_bars`."""

from __future__ import annotations

import logging

import pandas as pd

from data.clean import rules
from data.clean.errors import EmptyBars, MissingColumns

REQUIRED = ("symbol", "timestamp", "open", "high", "low", "close", "volume")
log = logging.getLogger("data.clean")


def clean_bars(df: pd.DataFrame) -> pd.DataFrame:
    """Return one bar per symbol per business day for the bars in `df`.

    Args:
        df: The BarFrame `data.ingest.fetch_bars` returns. Never mutated.

    Returns:
        A BarFrame with the same columns, sorted by `symbol, timestamp`.

    Raises:
        MissingColumns: A required column is absent.
        EmptyBars: `df` has no rows.
    """
    # Phase 1: validate.
    missing = [column for column in REQUIRED if column not in df.columns]
    if missing:
        raise MissingColumns(missing)
    if df.empty:
        raise EmptyBars()
    rows_in = len(df)

    # Phase 2: the rules, in design order.
    out = rules.dedupe(df)
    out = rules.drop_zero_volume(out)
    out, gaps_filled = rules.fill_gaps(out)
    out = out.sort_values(["symbol", "timestamp"], kind="stable").reset_index(drop=True)

    # Phase 3: log and return.
    log.info(
        "data.clean.done",
        extra={"rows_in": rows_in, "rows_out": len(out), "gaps_filled": gaps_filled},
    )
    return out.loc[:, list(REQUIRED)]
