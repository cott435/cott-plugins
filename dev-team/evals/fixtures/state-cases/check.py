#!/usr/bin/env python3
"""Run every state case through status.py and check its expectation.

Usage:  python3 check.py [case ...]

Builds each case (build.py) into a temporary directory, runs the plugin's status.py there
with the case's `args`, and checks `expect`:

- `section`, `state`, `ready`, `rounds`, `evidence` (a regex): the `<section> · …` row.
- `contains` / `absent`: substrings the output must / must not hold.
- `exit`: the exit code (default: not checked).

Prints PASS or FAIL per case, with the output on a FAIL, and exits 1 naming each failed case.
"""

from __future__ import annotations

import json
import re
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
STATUS = HERE.parents[2] / "skills" / "status" / "scripts" / "status.py"
sys.path.insert(0, str(HERE))
import build  # noqa: E402


def check(case: Path) -> list[str]:
    spec = json.loads((case / "case.json").read_text())
    exp = spec["expect"]
    with tempfile.TemporaryDirectory() as tmp:
        dest = build.build(case, Path(tmp).resolve() / "repo")
        res = subprocess.run([sys.executable, str(STATUS), *spec.get("args", [])],
                             cwd=dest, capture_output=True, text=True)
    out = res.stdout + res.stderr
    problems = []
    if "exit" in exp and res.returncode != exp["exit"]:
        problems.append(f"exit {res.returncode}, expected {exp['exit']}")
    if "section" in exp:
        row = next((line for line in res.stdout.splitlines() if line.startswith(f"{exp['section']} · ")), None)
        if row is None:
            problems.append(f"no row for {exp['section']}")
        else:
            cells = row.split(" · ")
            if "state" in exp and cells[1] != exp["state"]:
                problems.append(f"state {cells[1]!r}, expected {exp['state']!r}")
            if "ready" in exp and cells[3] != ("yes" if exp["ready"] else "no"):
                problems.append(f"ready {cells[3]!r}, expected {exp['ready']}")
            if "rounds" in exp and (0 if cells[4] == "—" else int(cells[4])) != exp["rounds"]:
                problems.append(f"round {cells[4]!r}, expected {exp['rounds']}")
            if "evidence" in exp and not re.search(exp["evidence"], cells[2]):
                problems.append(f"evidence {cells[2]!r} does not match {exp['evidence']!r}")
    for s in exp.get("contains", []):
        if s not in out:
            problems.append(f"missing {s!r}")
    for s in exp.get("absent", []):
        if s in out:
            problems.append(f"unexpected {s!r}")
    if problems:
        problems.append("output:\n    " + out.strip().replace("\n", "\n    "))
    return problems


def main() -> int:
    names = sys.argv[1:] or sorted(d.name for d in HERE.iterdir() if (d / "case.json").exists())
    failed = []
    for name in names:
        problems = check(HERE / name)
        print(f"{'PASS' if not problems else 'FAIL'}  {name}")
        for p in problems:
            print(f"      {p}")
        if problems:
            failed.append(name)
    print(f"\n{len(names) - len(failed)}/{len(names)} pass" + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
