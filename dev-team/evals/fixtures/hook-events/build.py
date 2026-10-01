#!/usr/bin/env python3
"""Build the repo the stop gate's cases run in: one built section, one proposed deviation.

Usage:  python3 build.py <dest>

Copies two-package/'s brief and dataset into dest (which must not exist), runs `git init`,
commits an empty root on `main`, and works on branch `build`. Commit 1 holds the contracts,
`docs/constraints.md` (Floor rows that pass with `ruff` on PATH), a section ledger
`docs/deviations/data/ingest.md` with
one `proposed` entry whose `Clause:` is `design §5 load_trades`, and the package skeleton.
Commit 2 holds `data/ingest` — code, README (one **Entry points and interfaces** row,
`` `load_trades` ``, `Public: yes`, which the contract's **Public surface (intent)** names),
`tests/intent/ingest/` with two tests, one
green and one red that cites `Design §5 load_trades`, and `tests/unit/ingest/` with one green
test — under the summary `data/ingest: …` and the trailer `Dev-Team-Run: run-package data`, so
the gate reads it as the run's own commit. Prints dest.

`run_sha(dest)` is the short sha of `HEAD`: check.py substitutes it for `{RUN_SHA}` in a
case's files, so a review report can name the run's commit.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TWO_PACKAGE = HERE.parent / "two-package"

ARCHITECTURE = """# Trade tape — architecture

Status: contracted

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| data | packages/data | — | load trades |

## Toolchain

```
ruff check packages/<pkg>
ruff format --check packages/<pkg>
```
"""

CONTRACT = """# data — package contract

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | read the export | packages/data/src/data/ingest | docs/packages/data/design/ingest.md | csv | — | — |
| surface | §4 Pipelines and §5 Public surface | packages/data/src/data | docs/packages/data/design/surface.md | — | ingest | — |

## Public surface (intent)

- `load_trades`, realized by ingest, consumed by the CLI
"""

CONSTRAINTS = """# Constraints

## Floor

| check | threshold | command | scope |
|---|---|---|---|
| lint | 0 errors | `ruff check packages/<pkg>` | package |
| format | clean | `ruff format --check packages/<pkg>` | package |

## Enforced

| dimension | threshold | command | scope |
|---|---|---|---|
| docstrings | 80% | `python3 -c "print('docstrings: 100%')"` | package |

## Measured

| dimension | current | target | command | scope |
|---|---|---|---|---|

## Guarded

- a new `# noqa`, `# type: ignore`, `# pragma: no cover`
- a new `@pytest.mark.skip` or `@pytest.mark.xfail` whose reason does not cite a `D<n>`
- a deleted or weakened assertion in an existing test
- a threshold in this file edited down

## Exceptions

| path or glob | check | reason | expires |
|---|---|---|---|
"""

DEVIATIONS = """# Deviations

## data/ingest — 2026-09-27 — deviation

- **Clause:** design §5 load_trades
- **Said:** "one dict per CSV row, with `price` as a float"
- **Did:** `price` is kept as the string the CSV holds
- **Why:** the contract's `Trade` shape says every field is a string
- **Status:** proposed
- **Raised by:** implementer — run-package data
- **Resolved by:** —
"""

PYPROJECT = """[project]
name = "data"
version = "0.1.0"
requires-python = ">=3.11"

[tool.pytest.ini_options]
pythonpath = ["src"]
testpaths = ["tests"]
"""

FILES_BASE = {
    ".gitignore": "__pycache__/\n.pytest_cache/\n.dev-team/\n",
    "docs/architecture.md": ARCHITECTURE,
    "docs/packages/data/contract.md": CONTRACT,
    "docs/constraints.md": CONSTRAINTS,
    "docs/deviations/data/ingest.md": DEVIATIONS,
    "packages/data/pyproject.toml": PYPROJECT,
    "packages/data/src/data/__init__.py": '"""The data package."""\n',
}

LOADER = '''"""Read the trade export."""

import csv
from pathlib import Path


def load_trades(path: str | Path) -> list[dict[str, str]]:
    """Return one dict per row of the CSV at ``path``."""
    with Path(path).open(newline="") as handle:
        return [dict(row) for row in csv.DictReader(handle)]
'''

TESTS = '''"""Intent tests for data/ingest."""

from pathlib import Path

from data.ingest import load_trades

HEADER = "ts,symbol,price,size,side\\n"
ROW = "2026-09-01T13:30:20Z,AAA,49.74,280,sell\\n"


def test_load_trades_reads_every_row(tmp_path: Path) -> None:
    """Design §4 read: one dict per CSV row."""
    csv_file = tmp_path / "trades.csv"
    csv_file.write_text(HEADER + ROW + ROW)
    assert len(load_trades(csv_file)) == 2


def test_load_trades_price_is_float(tmp_path: Path) -> None:
    """Design §5 load_trades: price is parsed to a float."""
    csv_file = tmp_path / "trades.csv"
    csv_file.write_text(HEADER + ROW)
    assert load_trades(csv_file)[0]["price"] == 49.74
'''

UNIT_TESTS = '''"""Unit tests for data/ingest."""

from pathlib import Path

from data.ingest.loader import load_trades


def test_load_trades_empty_file_has_no_rows(tmp_path: Path) -> None:
    """A header with no rows reads as no trades."""
    csv_file = tmp_path / "trades.csv"
    csv_file.write_text("ts,symbol,price,size,side\\n")
    assert load_trades(csv_file) == []
'''

README = """# ingest

## Purpose

Read the trade export.

## Entry points and interfaces

| name | signature | one-line use case | Public |
|---|---|---|---|
| `load_trades` | `load_trades(path)` | read the export | yes |
"""

FILES_RUN = {
    "packages/data/src/data/ingest/__init__.py": '"""Ingest."""\n\nfrom data.ingest.loader import load_trades\n\n__all__ = ["load_trades"]\n',
    "packages/data/src/data/ingest/loader.py": LOADER,
    "packages/data/src/data/ingest/README.md": README,
    "packages/data/tests/intent/ingest/test_loader.py": TESTS,
    "packages/data/tests/unit/ingest/test_loader_unit.py": UNIT_TESTS,
}


def _git(dest: Path, *args: str) -> None:
    subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid", *args],
                   cwd=dest, check=True, capture_output=True)


def _write(dest: Path, files: dict[str, str]) -> None:
    for rel, text in files.items():
        f = dest / rel
        f.parent.mkdir(parents=True, exist_ok=True)
        f.write_text(text)


def run_sha(dest: Path) -> str:
    """The short sha of `HEAD` in dest."""
    return subprocess.run(["git", "rev-parse", "--short", "HEAD"], cwd=dest, check=True,
                          capture_output=True, text=True).stdout.strip()


def build(dest: Path) -> Path:
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    (dest / "docs").mkdir(parents=True)
    (dest / "data").mkdir()
    shutil.copy(TWO_PACKAGE / "docs" / "brief.md", dest / "docs" / "brief.md")
    shutil.copy(TWO_PACKAGE / "data" / "trades.csv", dest / "data" / "trades.csv")
    _git(dest, "init", "-q", "-b", "main")
    _git(dest, "commit", "-q", "--allow-empty", "-m", "root")
    _git(dest, "checkout", "-q", "-b", "build")
    _write(dest, FILES_BASE)
    _git(dest, "add", "-A")
    _git(dest, "commit", "-q", "-m", "fixture: brief, dataset, contracts, constraints, one proposed deviation")
    _write(dest, FILES_RUN)
    _git(dest, "add", "packages")
    _git(dest, "commit", "-q", "-m", "data/ingest: loader, README", "-m", "Dev-Team-Run: run-package data")
    return dest


if __name__ == "__main__":
    if len(sys.argv) != 2:
        raise SystemExit("usage: build.py <dest>")
    print(build(Path(sys.argv[1]).resolve()))
