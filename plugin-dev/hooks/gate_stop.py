#!/usr/bin/env python3
"""Stop and SubagentStop: a phase committed without `phases.py finish` is checked before
its chat stops.

`phases.py brief` marks a phase as begun (`evals/workspace/run-phases/<slug>/active.json`,
with HEAD as it was) and `phases.py finish` removes the mark when it commits. A mark still
there, with a commit since whose subject carries `(phase N):`, means the phase was committed
by hand: this runs `phases.py check` and, when the commit is not HEAD, the tree is not clean
or the ledger row is not `done`, blocks the stop once (exit 2) with the reasons. A second
stop is let through (`stop_hook_active`), and `run-phases` runs the same check itself.

Exits 0 at once when the event's cwd is not in a plugin, no phase is marked, or the phase
has no commit yet: a chat stopping mid-phase for a review or a question is not held. A crash
or an unreadable event exits 0 with the reason on stderr.
"""
import json
import subprocess
import sys
from pathlib import Path

PHASES = Path(__file__).resolve().parent.parent / "scripts" / "phases.py"


def plugin_root(start):
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        if (d / ".claude-plugin" / "plugin.json").is_file():
            return d
    return None


def main():
    event = json.load(sys.stdin)
    root = plugin_root(event.get("cwd") or ".")
    if root is None:
        return 0
    marks = sorted((root / "evals" / "workspace" / "run-phases").glob("*/active.json"))
    if not marks or event.get("stop_hook_active"):
        return 0
    for mark in marks:
        data = json.loads(mark.read_text())
        n, slug = data["phase"], mark.parent.name
        log = subprocess.run(["git", "log", "--format=%s", f"{data['head']}..HEAD"],
                             cwd=root, capture_output=True, text=True).stdout
        if f"(phase {n}):" not in log:
            continue        # stopping mid-phase: nothing committed yet
        check = subprocess.run([sys.executable, str(PHASES), "check", slug, str(n)],
                               cwd=root, capture_output=True, text=True)
        if check.returncode == 0:
            mark.unlink()
            continue
        print(f"plugin-dev: {check.stdout.strip()}\nPut it right, then stop: the ledger row is "
              f"written and the phase committed by `python3 {PHASES} finish {slug} --what …`.",
              file=sys.stderr)
        return 2
    return 0


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:      # a gate that crashes must not hold the session
        print(f"plugin-dev stop gate: {type(e).__name__}: {e}; allowing", file=sys.stderr)
        sys.exit(0)
