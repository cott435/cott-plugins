"""Write cleaned bars to the landing directory as parquet."""

from datetime import date
from pathlib import Path

import pandas as pd

from data.clean.rules import BAR_COLUMNS


def bars_path(landing_dir: Path, symbol: str, run_date: date) -> Path:
    return landing_dir / symbol / f"{run_date.isoformat()}.parquet"


def write_bars(frame: pd.DataFrame, landing_dir: Path, symbol: str, run_date: date) -> Path:
    """Write `frame` (columns `BAR_COLUMNS`) and return the file written."""
    missing = set(BAR_COLUMNS) - set(frame.columns)
    if missing:
        raise ValueError(f"bars missing columns: {sorted(missing)}")
    path = bars_path(landing_dir, symbol, run_date)
    path.parent.mkdir(parents=True, exist_ok=True)
    frame.to_parquet(path, index=False)
    return path
