"""Cleaning rules for vendor bars. This section has no README on purpose."""

BAR_COLUMNS = ["ts", "symbol", "open", "high", "low", "close", "volume"]


def clean_bars(df):
    return df.loc[:, BAR_COLUMNS].dropna()
