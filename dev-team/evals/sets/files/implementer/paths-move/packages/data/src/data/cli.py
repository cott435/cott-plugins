"""The `data-daily` command."""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

from data.pipelines import daily


def main(argv: list[str] | None = None) -> int:
    """Run the `daily` pipeline on `--csv` and write the table's row count to stdout.

    Args:
        argv: the command line without the program name; `sys.argv[1:]` when `None`.

    Returns:
        0, or 1 when a section's error stopped the run; its message goes to stderr and
        nothing is written to stdout.
    """
    parser = argparse.ArgumentParser(prog="data-daily")
    parser.add_argument("--csv", type=Path, required=True)
    args = parser.parse_args(argv)
    try:
        table = daily(args.csv)
    except ValueError as exc:
        sys.stderr.write(f"data-daily: {exc}\n")
        return 1
    sys.stdout.write(f"{len(table)} trades\n")
    return 0
