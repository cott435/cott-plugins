"""Cleaning rules applied to raw bars before they are stored."""

import pandas as pd

from data.ingest.loader import RAW_COLUMNS

BAR_COLUMNS = (*RAW_COLUMNS, "adj_close")


def _drop_zero_volume(frame: pd.DataFrame) -> pd.DataFrame:
    return frame[frame["volume"] > 0]


def _dedupe_sessions(frame: pd.DataFrame) -> pd.DataFrame:
    return frame.drop_duplicates(subset="ts", keep="last")


def clean_bars(frame: pd.DataFrame) -> pd.DataFrame:
    """Drop zero-volume and duplicate sessions; add `adj_close` (no adjustment yet)."""
    cleaned = _dedupe_sessions(_drop_zero_volume(frame)).copy()
    cleaned["adj_close"] = cleaned["close"]
    return cleaned.reindex(columns=list(BAR_COLUMNS)).sort_values("ts").reset_index(drop=True)
