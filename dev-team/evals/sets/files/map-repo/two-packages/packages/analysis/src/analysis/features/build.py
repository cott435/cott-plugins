"""Per-symbol feature frames from cleaned bars."""

from datetime import date

import pandas as pd

from data import clean_bars, load_bars

FEATURE_COLUMNS = ("ts", "ret_1d", "vol_20d")


def build_features(symbol: str, start: date, end: date) -> pd.DataFrame:
    """One row per session with a one-day return and a 20-session volatility."""
    bars = clean_bars(load_bars(symbol, start, end))
    out = pd.DataFrame({"ts": bars["ts"]})
    out["ret_1d"] = bars["adj_close"].pct_change()
    out["vol_20d"] = out["ret_1d"].rolling(20).std()
    return out.reindex(columns=list(FEATURE_COLUMNS))
