#!/usr/bin/env python3
"""PostToolUse hook on Write|Edit: ruff format, then ruff check --fix, on a .py file the
dev-team implementer or tester just wrote.

Input: the hook JSON on stdin (`cwd`, `agent_type`, `tool_input.file_path`).

Exit 0 silently unless every one holds: `agent_type` is `dev-team:implementer` or
`dev-team:tester`; `<cwd>/docs/architecture.md` exists (the file that makes a directory a
dev-team repo; plugin hooks run in every session the plugin is enabled in); the path ends
`.py`, resolves under `cwd`, and is not under `docs/`.

In scope: `<ruff> format <path>`, `<ruff> check --fix <path>`, `<ruff> format <path>` again (a
fix that removes a line can leave the file unformatted, which the gate's Floor `ruff format
--check` row would then fail on), and a final `<ruff> check <path>` whose line numbers are the
file's as it now stands, all from `cwd`, where `<ruff>` is
`uv run ruff` when `<cwd>/uv.lock` exists and ruff runs that way, else `ruff` on PATH. When
neither runs, exit 0: a PostToolUse hook cannot block anyway. When the check still fails,
print what it left to stderr under one line naming the file and exit 2, so the model sees it;
the edit stands. Malformed or empty stdin: exit 0.
"""

from __future__ import annotations

import json
import subprocess
import sys
from pathlib import Path

ROLES = ("dev-team:implementer", "dev-team:tester")


def _ruff(cwd: Path) -> list[str] | None:
    """The ruff command that runs here, or None when none does."""
    candidates = ([["uv", "run", "ruff"]] if (cwd / "uv.lock").exists() else []) + [["ruff"]]
    for cmd in candidates:
        try:
            if subprocess.run([*cmd, "--version"], cwd=cwd, capture_output=True, timeout=60).returncode == 0:
                return cmd
        except (OSError, subprocess.TimeoutExpired):
            continue
    return None


def main() -> int:
    try:
        event = json.loads(sys.stdin.read())
        cwd = Path(event["cwd"]).resolve()
        agent = event.get("agent_type") or ""
        raw = (event.get("tool_input") or {}).get("file_path") or ""
    except (ValueError, KeyError, TypeError, AttributeError):
        return 0
    if agent not in ROLES or not (cwd / "docs" / "architecture.md").exists() or not raw.endswith(".py"):
        return 0
    path = Path(raw) if Path(raw).is_absolute() else cwd / raw
    try:
        rel = path.resolve().relative_to(cwd)
    except ValueError:
        return 0
    if rel.parts[:1] == ("docs",) or not path.exists():
        return 0
    ruff = _ruff(cwd)
    if ruff is None:
        return 0
    try:
        subprocess.run([*ruff, "format", str(rel)], cwd=cwd, capture_output=True, timeout=60)
        subprocess.run([*ruff, "check", "--fix", str(rel)], cwd=cwd, capture_output=True, timeout=60)
        subprocess.run([*ruff, "format", str(rel)], cwd=cwd, capture_output=True, timeout=60)
        check = subprocess.run([*ruff, "check", "--output-format", "concise", str(rel)],
                               cwd=cwd, capture_output=True, text=True, timeout=60)
    except (OSError, subprocess.TimeoutExpired):
        return 0
    if check.returncode == 0:
        return 0
    print(f"dev-team format hook: ruff check left these in {rel.as_posix()}:", file=sys.stderr)
    print((check.stdout or check.stderr).rstrip(), file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
