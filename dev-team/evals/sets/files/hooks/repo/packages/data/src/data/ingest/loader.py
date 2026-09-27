"""Read the trade export."""

import csv
from pathlib import Path

FIELDS = ("ts", "symbol", "price", "size", "side")


def load_trades(path: str | Path) -> list[dict[str, str]]:
    """Return one dict per row of the CSV at ``path``.

    Rejecting a row with a missing field (design §6) is not built yet, which is what
    makes one intent test red for the gate eval.
    """
    with Path(path).open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]
