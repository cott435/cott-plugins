#!/usr/bin/env python3
"""Run one command while holding `.dev-team/locks/<name>/` in the current directory, a mkdir lock.

Usage:  python3 locked.py <name> -- <command> [args…]

Agents run in parallel and two of them editing `pyproject.toml`, `uv.lock` or the root
`.gitignore` at once lose one another's lines; this is the one way an implementer touches those
files (implementer.md, **Files outside your section**). `<name>` is `[a-z0-9-]+` — `deps` for
`uv add` and for `entry_point.py`, the third shared edit (one entry-point line in the package
`pyproject.toml`), `gitignore` for the `.gitignore` block. Waits up to 600 s polling every
0.2 s; a lock older than 600 s is a crashed holder's and is removed. Exits with the command's
exit code; 2 on usage; 75 when the wait runs out. The command inherits stdin, stdout and stderr and runs in the
current directory. `guard_bash.py` lets a command through when its program is this script.
"""

from __future__ import annotations

import os
import re
import subprocess
import sys
import time
from pathlib import Path

WAIT = 600.0  # seconds to wait for the lock
POLL = 0.2
STALE = 600.0  # a lock directory older than this is a crashed holder's
EX_TEMPFAIL = 75
USAGE = "usage: python3 locked.py <name> -- <command> [args…]   (<name> is [a-z0-9-]+)"


def acquire(lock: Path) -> bool:
    """mkdir the lock, breaking a stale one; False when WAIT runs out."""
    lock.parent.mkdir(parents=True, exist_ok=True)
    deadline = time.monotonic() + WAIT
    while True:
        try:
            os.mkdir(lock)
            return True
        except FileExistsError:
            try:
                if time.time() - lock.stat().st_mtime > STALE:
                    os.rmdir(lock)
                    continue
            except OSError:
                continue  # released or broken between the mkdir and the stat: try again
        if time.monotonic() >= deadline:
            return False
        time.sleep(POLL)


def main(argv: list[str]) -> int:
    if len(argv) < 3 or argv[1] != "--" or not re.fullmatch(r"[a-z0-9-]+", argv[0]):
        print(USAGE, file=sys.stderr)
        return 2
    lock = Path.cwd() / ".dev-team" / "locks" / argv[0]
    if not acquire(lock):
        print(f"locked.py: gave up after {WAIT:.0f}s waiting for {lock}", file=sys.stderr)
        return EX_TEMPFAIL
    try:
        return subprocess.run(argv[2:]).returncode
    except OSError as exc:
        print(f"locked.py: cannot run {argv[2]}: {exc}", file=sys.stderr)
        return 127
    finally:
        try:
            os.rmdir(lock)
        except OSError:
            pass


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
