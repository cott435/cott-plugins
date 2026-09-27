"""Per-account totals and the summary file."""

from collections import defaultdict
from decimal import Decimal
from pathlib import Path

from app.clean.normalize import CleanRow


def summarize(rows: list[CleanRow]) -> dict[str, Decimal]:
    totals: dict[str, Decimal] = defaultdict(Decimal)
    for row in rows:
        totals[row.account] += row.amount
    return dict(sorted(totals.items()))


def write_summary(totals: dict[str, Decimal], report_dir: Path, name: str) -> Path:
    report_dir.mkdir(parents=True, exist_ok=True)
    path = report_dir / f"{name}.md"
    lines = [f"# {name}", ""] + [f"- {account}: {amount}" for account, amount in totals.items()]
    path.write_text("\n".join(lines) + "\n")
    return path
