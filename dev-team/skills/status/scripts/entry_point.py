#!/usr/bin/env python3
"""Add or replace one entry-point line in a package's pyproject.toml.

Usage:  python3 locked.py deps -- python3 entry_point.py <pkg> <group> <name> <target>

Run from the repo root, under the `deps` lock (locked.py): parallel implementers share the
package `pyproject.toml`, and only the lock serialises them. Writes the line
`<name> = "<target>"` under `[project.entry-points."<group>"]` in `<package root>/pyproject.toml`,
creating the table when it is absent, then runs `uv sync --all-packages` when the repo root
has a `uv.lock`. Standard library only; the file is edited as text and parsed with `tomllib`
before it is kept, so comments and order survive.

Refused, exit 2 with the reason on stderr: a `<target>` whose module is not `<pkg>` or under
it; a module whose file does not exist yet (`<top>/<path>.py` or `<top>/<path>/__init__.py`,
`<top>` the directory holding the package's import root); the groups `console_scripts` and
`gui_scripts`, which are `[project.scripts]` and the surface section's; a `<pkg>` with no
`pyproject.toml` at its root; a `<group>` or `<name>` outside `[A-Za-z0-9_.-]+`.

Exits 0 printing `entry point: [<group>] <name> = <target> in <path>`, or `entry point
unchanged: …` when the line is already there (no sync); 1 when the edited file does not parse
or does not hold the entry, with the file restored; else `uv sync`'s exit code.
"""

from __future__ import annotations

import re
import subprocess
import sys
import tomllib
from pathlib import Path

sys.dont_write_bytecode = True  # no __pycache__ inside the installed plugin
sys.path.insert(0, str(Path(__file__).resolve().parent))
import status  # noqa: E402

USAGE = "usage: python3 entry_point.py <pkg> <group> <name> <target>   (<target> is module or module:attr)"
TOKEN = re.compile(r"[A-Za-z0-9_.-]+")
BARE = re.compile(r"[A-Za-z0-9_-]+")
SCRIPTS_GROUPS = ("console_scripts", "gui_scripts")
HEADER = re.compile(r"\[\[?[^\[\]]+\]\]?\s*(?:#.*)?")


def _refuse(reason: str) -> int:
    print(f"entry_point.py: {reason}", file=sys.stderr)
    return 2


def import_top(pkg: str) -> Path:
    """The directory holding the package's import root: the parent of the `surface` row's path,
    as surface_check resolves it."""
    row = status._row(pkg, "surface")
    top = status.ROOT / row["path"] if row else status.package_root(pkg) / "src" / pkg
    return top.parent


def module_file(top: Path, module: str) -> Path | None:
    base = top.joinpath(*module.split("."))
    for f in (base.with_name(base.name + ".py"), base / "__init__.py"):
        if f.is_file():
            return f
    return None


def _is_header(line: str) -> bool:
    return HEADER.fullmatch(line.strip()) is not None


def _table(lines: list[str], *headers: str) -> tuple[int, int] | None:
    """(header index, end index) of the first table whose header line is one of headers."""
    for i, line in enumerate(lines):
        if line.split("#")[0].strip() in headers:
            end = next((j for j in range(i + 1, len(lines)) if _is_header(lines[j])), len(lines))
            return i, end
    return None


def _last_filled(lines: list[str], start: int, end: int) -> int:
    """The index after the last non-blank line in lines[start:end]."""
    for j in range(end - 1, start - 1, -1):
        if lines[j].strip():
            return j + 1
    return start + 1


def _insert(lines: list[str], at: int, block: list[str]) -> list[str]:
    if at > 0 and not lines[at - 1].endswith("\n"):
        lines[at - 1] += "\n"
    return lines[:at] + block + lines[at:]


def edit(text: str, group: str, name: str, target: str) -> str:
    """text with `<name> = "<target>"` under the group's table, added or replaced."""
    key = name if BARE.fullmatch(name) else f'"{name}"'
    entry = f'{key} = "{target}"\n'
    lines = text.splitlines(keepends=True)
    headers = [f'[project.entry-points."{group}"]']
    if BARE.fullmatch(group):
        headers.append(f"[project.entry-points.{group}]")
    found = _table(lines, *headers)
    if found:
        start, end = found
        keyed = re.compile(rf'\s*("?){re.escape(name)}\1\s*=')
        for j in range(start + 1, end):
            if keyed.match(lines[j]):
                lines[j] = entry if lines[j].endswith("\n") else entry.rstrip("\n")
                return "".join(lines)
        return "".join(_insert(lines, _last_filled(lines, start, end), [entry]))
    block = [f'[project.entry-points."{group}"]\n', entry]
    scripts = _table(lines, "[project.scripts]")
    if scripts:
        at = _last_filled(lines, *scripts)
    else:
        build = _table(lines, "[build-system]")
        at = build[0] if build else len(lines)
    if at > 0 and lines[at - 1].strip():
        block.insert(0, "\n")
    if at < len(lines) and lines[at].strip():
        block.append("\n")
    return "".join(_insert(lines, at, block))


def holds(text: str, group: str, name: str, target: str) -> bool:
    try:
        data = tomllib.loads(text)
    except tomllib.TOMLDecodeError:
        return False
    return data.get("project", {}).get("entry-points", {}).get(group, {}).get(name) == target


def main(argv: list[str]) -> int:
    if len(argv) != 4:
        print(USAGE, file=sys.stderr)
        return 2
    pkg, group, name, target = argv
    if not TOKEN.fullmatch(group):
        return _refuse(f"group {group!r} is outside [A-Za-z0-9_.-]+")
    if not TOKEN.fullmatch(name):
        return _refuse(f"name {name!r} is outside [A-Za-z0-9_.-]+")
    if group in SCRIPTS_GROUPS:
        return _refuse(f"{group} is [project.scripts], the surface section's; it is not added here")
    status.set_root(Path.cwd())
    pyproject = status.package_root(pkg) / "pyproject.toml"
    if not pyproject.is_file():
        return _refuse(f"{pkg} has no pyproject.toml at {status._rel(pyproject)}")
    module = target.split(":", 1)[0]
    if module != pkg and not module.startswith(pkg + "."):
        return _refuse(f"{target}: module {module} is not {pkg} or under it")
    top = import_top(pkg)
    if module_file(top, module) is None:
        path = status._rel(top.joinpath(*module.split(".")))
        return _refuse(f"{target}: module {module} has no file yet ({path}.py or {path}/__init__.py); "
                       "add the entry point in the commit that adds the module")
    shown = f"[{group}] {name} = {target} in {status._rel(pyproject)}"
    before = pyproject.read_bytes()
    text = before.decode()
    after = edit(text, group, name, target)
    if after == text:
        print(f"entry point unchanged: {shown}")
        return 0
    if not holds(after, group, name, target):
        print(f"entry_point.py: the edited {status._rel(pyproject)} does not parse or does not hold the entry; "
              "left as it was", file=sys.stderr)
        pyproject.write_bytes(before)
        return 1
    pyproject.write_bytes(after.encode())
    print(f"entry point: {shown}")
    if (status.ROOT / "uv.lock").exists():
        sys.stdout.flush()
        try:
            return subprocess.run(["uv", "sync", "--all-packages"], cwd=status.ROOT).returncode
        except OSError as exc:
            print(f"entry_point.py: cannot run uv sync: {exc}", file=sys.stderr)
            return 127
    return 0


if __name__ == "__main__":
    sys.exit(main(sys.argv[1:]))
