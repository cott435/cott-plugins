"""The package's command: `load`, run as `data-load`."""

from __future__ import annotations

import sys

from data.pipelines.load import run_load


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
