"""The three cleaning rules, in the order `clean_bars` applies them."""

from __future__ import annotations

import pandas as pd

from data.clean.calendar import trading_days

PRICE_COLUMNS = ["open", "high", "low", "close"]


def dedupe(df: pd.DataFrame) -> pd.DataFrame:
    """Resolve duplicate bars, keeping the row with the higher volume.

    Departs from design §4 step 2 (keep the first row): the later vendor row is the
    end-of-day correction. See docs/deviations.md, data/clean — 2026-09-24.
    """
    ordered = df.sort_values(["timestamp", "volume"], ascending=[True, False], kind="stable")
    return ordered.drop_duplicates(subset=["timestamp"], keep="first").reset_index(drop=True)


def drop_zero_volume(df: pd.DataFrame) -> pd.DataFrame:
    """Return the frame with zero-volume rows kept as the vendor sent them.

    See docs/deviations.md, data/clean — 2026-09-25.
    """
    return df


def fill_gaps(df: pd.DataFrame) -> tuple[pd.DataFrame, int]:
    """Insert a bar for every trading day between a symbol's first and last bar.

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
        full[PRICE_COLUMNS] = full[PRICE_COLUMNS].ffill()
        full["volume"] = full["volume"].fillna(0).astype("int64")
        full["symbol"] = symbol
        frames.append(full.rename_axis("timestamp").reset_index())
    return pd.concat(frames, ignore_index=True), filled
