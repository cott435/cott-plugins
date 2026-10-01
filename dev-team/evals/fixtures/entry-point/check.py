#!/usr/bin/env python3
"""Run skills/status/scripts/entry_point.py against a built repo and check what it did.

Usage:  python3 check.py

Builds one temporary repo: `docs/architecture.md` with the Packages row `core | packages/core`,
`docs/packages/core/contract.md` with `testing` and `surface` rows, `packages/core/pyproject.toml`
in workspace-scaffold §2's shape (one comment line, a `[project.scripts]` table), and
`packages/core/src/core/testing/plugin.py` (with the `__init__.py` files that make `core` and
`core.testing` modules). CASES run in order against that repo, each from the repo root, with
no lock and no `uv.lock`, so no `uv sync` runs. Prints PASS or FAIL per case, then `<n>/<n>
pass`; exit 1 on any failure.
"""

from __future__ import annotations

import subprocess
import sys
import tempfile
import tomllib
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parents[2] / "skills" / "status" / "scripts" / "entry_point.py"
PYPROJECT = "packages/core/pyproject.toml"

ARCH = "# Architecture\n\n## Packages\n\n| package | path | depends on | covers |\n|---|---|---|---|\n| core | packages/core | — | the core |\n"
CONTRACT = ("# core — package contract\n\n## Sections\n\n"
            "| section | responsibility | path | owner doc | builds with | depends on | source |\n"
            "|---|---|---|---|---|---|---|\n"
            "| testing | a pytest plugin | packages/core/src/core/testing | docs/packages/core/design/testing.md | pytest | — | — |\n"
            "| surface | §4 Pipelines and §5 Public surface | packages/core/src/core | docs/packages/core/design/surface.md | — | testing | — |\n")
COMMENT = "# upstream packages by name; resolved from the workspace via the root's [tool.uv.sources]\n"
SCRIPTS = ('[project.scripts]\n'
           '# <pkg>-<verb> = "<pkg>.cli:<function>"   — added by the surface section\'s implementer\n'
           'core-run = "core.cli:main"\n')
PY = ('[project]\nname = "core"\nversion = "0.1.0"\nrequires-python = ">=3.12"\ndependencies = [\n'
      '    "pydantic>=2",\n    ' + COMMENT + ']\n\n' + SCRIPTS +
      '\n[build-system]\nrequires = ["hatchling"]\nbuild-backend = "hatchling.build"\n\n'
      '[tool.hatch.build.targets.wheel]\npackages = ["src/core"]\n')
FILES = {
    "docs/architecture.md": ARCH,
    "docs/packages/core/contract.md": CONTRACT,
    PYPROJECT: PY,
    "packages/core/src/core/__init__.py": "",
    "packages/core/src/core/testing/__init__.py": "",
    "packages/core/src/core/testing/plugin.py": "def hook():\n    pass\n",
}


def _eps(text: str) -> dict:
    return tomllib.loads(text).get("project", {}).get("entry-points", {})


def new_table(res, before: str, after: str) -> list[str]:
    out = []
    if _eps(after).get("pytest11", {}).get("core_testing") != "core.testing.plugin":
        out.append("the entry is not in the parsed file")
    if COMMENT not in after:
        out.append("the comment line changed")
    if SCRIPTS not in after:
        out.append("[project.scripts] changed")
    if not after.index("[project.scripts]") < after.index('[project.entry-points."pytest11"]') < after.index("[build-system]"):
        out.append("the new table is not after [project.scripts] (and before [build-system])")
    if '\n\n[project.entry-points."pytest11"]\ncore_testing = "core.testing.plugin"\n\n[build-system]' not in after:
        out.append("the new table is not set off by one blank line before and after")
    return out


def second_name(res, before: str, after: str) -> list[str]:
    table = _eps(after).get("pytest11", {})
    out = [] if table == {"core_testing": "core.testing.plugin", "other": "core.testing.plugin"} else [f"table {table}"]
    if after.count("[project.entry-points.") != 1:
        out.append("more than one entry-point table")
    return out


def replace(res, before: str, after: str) -> list[str]:
    out = []
    if _eps(after).get("pytest11", {}).get("core_testing") != "core.testing.plugin:hook":
        out.append("core_testing does not point at core.testing.plugin:hook")
    if sum(1 for ln in after.splitlines() if ln.startswith("core_testing")) != 1:
        out.append("not exactly one core_testing line")
    return out


def unchanged(res, before: str, after: str) -> list[str]:
    out = [] if after == before else ["the file's bytes changed"]
    if "entry point unchanged" not in res.stdout:
        out.append(f"stdout {res.stdout.strip()!r}")
    return out


def dotted_name(res, before: str, after: str) -> list[str]:
    out = []
    if '[project.entry-points."pt.migrations"]\n"core.testing" = "core.testing"\n' not in after:
        out.append("no quoted header with a quoted key")
    if _eps(after).get("pt.migrations", {}).get("core.testing") != "core.testing":
        out.append("the entry is not in the parsed file")
    return out


def same_file(res, before: str, after: str) -> list[str]:
    return [] if after == before else ["the file changed"]


# (case, arguments, expected exit, judge)
CASES = (
    ("new-table", ["core", "pytest11", "core_testing", "core.testing.plugin"], 0, new_table),
    ("second-name", ["core", "pytest11", "other", "core.testing.plugin"], 0, second_name),
    ("replace", ["core", "pytest11", "core_testing", "core.testing.plugin:hook"], 0, replace),
    ("unchanged", ["core", "pytest11", "core_testing", "core.testing.plugin:hook"], 0, unchanged),
    ("dotted-name", ["core", "pt.migrations", "core.testing", "core.testing"], 0, dotted_name),
    ("outside-package", ["core", "pytest11", "x", "other.plugin"], 2, same_file),
    ("missing-module", ["core", "pytest11", "x", "core.nothere"], 2, same_file),
    ("console-scripts", ["core", "console_scripts", "x", "core.testing.plugin"], 2, same_file),
)


def main() -> int:
    failed = []
    with tempfile.TemporaryDirectory() as tmp:
        repo = Path(tmp).resolve() / "repo"
        for rel, text in FILES.items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text)
        for name, args, code, judge in CASES:
            before = (repo / PYPROJECT).read_text()
            res = subprocess.run([sys.executable, str(SCRIPT), *args], cwd=repo, capture_output=True, text=True,
                                 env={"PATH": "/usr/bin:/bin", "PYTHONDONTWRITEBYTECODE": "1"})
            after = (repo / PYPROJECT).read_text()
            problems = [] if res.returncode == code else [f"exit {res.returncode}, expected {code}"]
            problems += judge(res, before, after)
            print(f"{'PASS' if not problems else 'FAIL'}  {name}")
            for p in problems:
                print(f"      {p}")
            if problems:
                print(f"      stdout: {res.stdout.strip()!r}\n      stderr: {res.stderr.strip()!r}")
                failed.append(name)
    print(f"\n{len(CASES) - len(failed)}/{len(CASES)} pass" + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
