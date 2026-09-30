"""Read the trade export."""

import csv
from pathlib import Path

FIELDS = ("ts", "symbol", "price", "size", "side")


def load_trades(path: str | Path) -> list[dict[str, str]]:
    """Return one dict per row of the CSV at ``path``.

    A row with an empty field raises ``ValueError`` naming the field (design §6). This is
    the loader `build.sh --green` installs, so the section's intent suite passes and the
    stop gate lets a guard eval's stub finish at its first stop.
    """
    rows = []
    with Path(path).open(newline="") as handle:
        for row in csv.DictReader(handle):
            missing = [name for name in FIELDS if not row.get(name)]
            if missing:
                raise ValueError(f"missing field: {missing[0]}")
            rows.append(dict(row))
    return rows
