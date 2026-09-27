"""The three cleaning rules, in the order `clean_bars` applies them."""

from __future__ import annotations

import pandas as pd

from data.clean.calendar import trading_days

PRICE_COLUMNS = ["open", "high", "low", "close"]


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """Resolve duplicate bars, keeping the row with the higher volume.

    A duplicate is the same `(symbol, timestamp)` pair (D1). Departs from design §4 step 2
    (keep the first row): the later vendor row is the end-of-day correction. See
    docs/deviations.md, data/clean — 2026-09-24 (approved).
    """
    ordered = df.sort_values(["symbol", "timestamp", "volume"], ascending=[True, True, False], kind="stable")
    return ordered.drop_duplicates(subset=["symbol", "timestamp"], keep="first").reset_index(drop=True)


def drop_zero_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Drop every row whose volume is 0, so the day is filled like a missing one."""
    return df[df["volume"] > 0].reset_index(drop=True)


def fill_gaps(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Insert a bar for every trading day between a symbol's first and last bar.

    A filled bar opens and closes at the previous bar's close with volume 0.

    Returns:
        The filled frame and the number of rows inserted.
    """
    frames = []
    filled = 0
    for symbol, part in df.groupby("symbol", sort=False):
        part = part.set_index("timestamp").sort_index()
        index = trading_days(part.index.min(), part.index.max())
        full = part.reindex(index)
        gaps = full["close"].isna()
        filled += int(gaps.sum())
        previous_close = full["close"].ffill()
        full["close"] = previous_close
        full["open"] = full["open"].where(~gaps, previous_close)
        full[["high", "low"]] = full[["high", "low"]].ffill()
        full["volume"] = full["volume"].fillna(0).astype("int64")
        full["symbol"] = symbol
        frames.append(full.rename_axis("timestamp").reset_index())
    return pd.concat(frames, ignore_index=True), filled
