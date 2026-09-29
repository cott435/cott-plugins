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

The rules are the repo's own when it has them: a `ruff.toml`, `.ruff.toml`, or a
`pyproject.toml` with a `[tool.ruff` table at `cwd`. Until the first implementer merges the
plugin's `pyproject-lint-config.toml` into the root `pyproject.toml`, it has none, and ruff's
defaults would pass what the real rules later fail: a tester writes intent tests nobody may
edit afterwards, so their lint errors fail every later section's gate. So with no repo
config, every ruff call gets `--config` pointing at a copy of that file named
`pyproject.toml` (ruff reads the `[tool.ruff]` form only from a file of that name).
"""

from __future__ import annotations

import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

ROLES = ("dev-team:implementer", "dev-team:tester")
PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parents[1])
LINT_BLOCK = PLUGIN_ROOT / "pyproject-lint-config.toml"


def _has_config(cwd: Path) -> bool:
    """Whether the repo root carries ruff settings of its own."""
    if (cwd / "ruff.toml").exists() or (cwd / ".ruff.toml").exists():
        return True
    try:
        return "[tool.ruff" in (cwd / "pyproject.toml").read_text()
    except OSError:
        return False


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
    with tempfile.TemporaryDirectory() as tmp:
        config: list[str] = []
        if not _has_config(cwd) and LINT_BLOCK.exists():
            shutil.copy(LINT_BLOCK, Path(tmp) / "pyproject.toml")
            config = ["--config", str(Path(tmp) / "pyproject.toml")]
        try:
            subprocess.run([*ruff, "format", *config, str(rel)], cwd=cwd, capture_output=True, timeout=60)
            subprocess.run([*ruff, "check", *config, "--fix", str(rel)], cwd=cwd, capture_output=True, timeout=60)
            subprocess.run([*ruff, "format", *config, str(rel)], cwd=cwd, capture_output=True, timeout=60)
            check = subprocess.run([*ruff, "check", *config, "--output-format", "concise", str(rel)],
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
