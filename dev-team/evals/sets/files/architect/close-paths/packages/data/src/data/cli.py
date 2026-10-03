"""The package's commands: `load`, run as `data-load`, and `verify`, run as `data-verify`."""

from __future__ import annotations

import sys

from data.pipelines.load import run_load
from data.pipelines.verify import run_verify


def load() -> int:
    """Load the trades CSV named on the command line into the trades database.

    Takes `SOURCE` and `TARGET` from the command line and runs the `load` pipeline on
    them.

    Returns:
        0 when the run finished.
    """
    source, target = sys.argv[1], sys.argv[2]
    run_load(source, target)
    return 0


def verify() -> int:
    """Verify every vendor file in the drop directory named on the command line.

    Takes `SOURCE_DIR` from the command line and runs the `verify` pipeline on it.

    Returns:
        0 when every file carries the vendor header, 1 otherwise.
    """
    failures = run_verify(sys.argv[1])
    return 1 if failures else 0
