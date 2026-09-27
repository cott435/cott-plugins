import csv
from collections.abc import Iterable, Iterator
from datetime import datetime
from pathlib import Path

from data.ingest.errors import IngestError
from data.ingest.models import Bar

COLUMNS = ("symbol", "timestamp", "open", "high", "low", "close", "volume")


def discover_files(root: Path) -> list[Path]:
    return sorted(root.rglob("*.csv"))


def load_bars(paths: Iterable[Path]) -> Iterator[Bar]:
    for path in paths:
        with path.open(newline="") as handle:
            reader = csv.DictReader(handle)
            missing = [c for c in COLUMNS if c not in (reader.fieldnames or [])]
            if missing:
                raise IngestError("data.ingest.missing_column", str(path), {"missing": missing})
            for row in reader:
                try:
                    yield Bar(
                        symbol=row["symbol"],
                        ts=datetime.fromisoformat(row["timestamp"]),
                        open=float(row["open"]),
                        high=float(row["high"]),
                        low=float(row["low"]),
                        close=float(row["close"]),
                        volume=int(row["volume"]),
                    )
                except ValueError as exc:
                    raise IngestError("data.ingest.malformed_row", str(path), {"row": row}) from exc
