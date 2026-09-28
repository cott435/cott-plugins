#!/usr/bin/env python3
"""Regenerate status-repo.txt: the real `status.py --repo` over documenter eval 3's repo.

Usage:  python3 build_status_repo.py [--keep <dest>]

The eval's repo is `repo/` overlaid with `repo-gaps/` (the overlay's own README.md is left
out: it describes the fixture, not the repo). That union holds the documents the documenter
reads, but not the loop's state — designs, intent trees, review reports and the commit order
between them — so `status.py` alone would read every package as `planned`. This script adds
that state in a scratch git repository, one commit per loop step, so the script derives what
the fixture says: `data` shipped (ingest, clean and surface DONE), `analysis` building with
`features` DONE and `surface` undesigned, `report` with no contract. None of the added files
is part of the fixture the executor reads. Writes status-repo.txt beside this file; with
--keep, the scratch repository is left at dest.
"""

from __future__ import annotations

import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[3]
STATUS = PLUGIN / "skills" / "status" / "scripts" / "status.py"
DATE = "2026-09-12"

DONE = [
    ("data", "ingest", "packages/data"),
    ("data", "clean", "packages/data"),
    ("data", "surface", "packages/data"),
    ("analysis", "features", "packages/analysis"),
]


def git(repo: Path, *args: str) -> str:
    out = subprocess.run(
        ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.com", *args],
        cwd=repo, capture_output=True, text=True, check=True,
    )
    return out.stdout.strip()


def commit(repo: Path, files: dict[str, str], message: str) -> str:
    for rel, text in files.items():
        p = repo / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text)
    git(repo, "add", "-A")
    git(repo, "commit", "-q", "-m", message)
    return git(repo, "rev-parse", "HEAD")


def build(repo: Path) -> None:
    union = repo.parent / "union"
    shutil.copytree(HERE / "repo", union)
    shutil.copytree(HERE / "repo-gaps", union, dirs_exist_ok=True)
    (union / "README.md").unlink()
    files = {f.relative_to(union).as_posix(): f.read_text() for f in union.rglob("*") if f.is_file()}
    shutil.rmtree(union)
    built = {k: v for k, v in files.items() if k.startswith("packages/") or k.endswith("/interface.md")}
    repo.mkdir(parents=True)
    git(repo, "init", "-q", "-b", "main")
    probe = "# Source — vendor\n\n## Access\n\n`DATA_VENDOR_KEY`.\n\n## data/ingest\n\n`/v1/bars` — observed.\n"
    commit(repo, {**{k: v for k, v in files.items() if k not in built}, "docs/sources/vendor.md": probe},
           "fixture: contracts, ledgers, probe doc")
    commit(repo, {f"docs/packages/{p}/design/{s}.md": f"Mode: new\n\n# {p}/{s} — design\n" for p, s, _ in DONE},
           "fixture: designs")
    commit(repo, {f"{root}/tests/intent/{s}/test_{s}.py": f'def test_{s}():\n    """Design §5 {s}: stub."""\n'
                  for _, s, root in DONE}, "fixture: intent tests")
    code = commit(repo, built, "fixture: code, section READMEs, interface.md")
    commit(repo, {f"docs/reviews/{DATE}-{p}-{s}-r1-{x}.md":
                  f"Scope: {p}/{s}\nCommit: {code[:7]}\nVerdict: approve\nRound: 1\nFocus: {focus}\n"
                  for p, s, _ in DONE for x, focus in (("a", "conformance"), ("b", "correctness"))},
           "fixture: round-1 reviews, all approve")


def main() -> int:
    keep = sys.argv[sys.argv.index("--keep") + 1] if "--keep" in sys.argv else None
    tmp = Path(tempfile.mkdtemp())
    repo = Path(keep) if keep else tmp / "repo"
    try:
        build(repo)
        out = subprocess.run([sys.executable, str(STATUS), "--repo"], cwd=repo, capture_output=True, text=True)
        if out.returncode != 0:
            sys.stderr.write(out.stdout + out.stderr)
            return 1
        (HERE / "status-repo.txt").write_text(out.stdout)
        sys.stdout.write(out.stdout)
    finally:
        shutil.rmtree(tmp, ignore_errors=True)
    return 0


if __name__ == "__main__":
    sys.exit(main())
