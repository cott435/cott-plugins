#!/usr/bin/env python3
"""Build one state case as a git repository, so status.py can be run against it.

Usage:  python3 build.py <case> <dest>

Copies two-package/'s brief and dataset into dest (which must not exist), runs `git init`,
commits an empty root on `main`, creates branch `build` (unless the case says
`"branch": "main"`), commits the brief and dataset, then applies the case's steps in order,
one commit per step, so commit order is the evidence. Files listed under the case's `dirty`
are written last and left uncommitted. A top-level `gate` key maps a section to the text of
its stop-gate record, written to `.dev-team/gate/data/<section>.txt` after `dirty`, with
`{SECTION}` replaced by the first seven characters of the newest commit touching
`packages/data/src/data/<section>` and `packages/data/tests/unit/<section>`; the key also adds
`.dev-team/` to `.git/info/exclude`, as a scaffolded repo's `.gitignore` would. Prints dest.

A step is either explicit, `{"files": {"<path>": "<content>"}, "message": "<summary>"}`, or a
macro, `{"do": "<macro>", ...}`; the macros are the functions named `m_<macro>` below. In any
file content, `{HEAD}` is replaced with the sha of the commit the step is made on top of — the
`Commit:` a reviewer writes is the code it reviewed, not its own report's commit.

`review`, `deviation` and `change` take `"layout": "new" | "old"` (default `new`): `new` writes
the 2.2 paths under `docs/packages/<pkg>/` and the ledger heading's `— <k>`; `old` the 2.0
paths and heading. `edit` takes `path`, `message`, and `append` (text added at the end),
`"replace": ["<old>", "<new>"]` (the first occurrence, applied before `append`), or both.
`base` takes `call_paths: true` (a **Call paths** heading matching the `commands` macro's tree)
or a string (the heading's body verbatim), and `stage: true` (2.7): the `clean` row's `source`
`stage:rawtrades` and `builds with` `dev-team:data-quality`, and a **Package conventions**
line for the stage at the contract's end. `profile` writes `docs/sources/rawtrades.md`, a
data profile serving `data/<section>` (default `clean`), one round line per entry of `lines`:
a verdict string (round 0, commit `none`) or `{"round": r, "commit": "{HEAD}" | "none",
"verdict": "…"}`; with `append: true` it adds only the lines.
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
TWO_PACKAGE = HERE.parent / "two-package"
PKG = "data"
DATE = "2026-09-27"

ARCHITECTURE = """# Architecture — trade tape

## Packages

| package | path | depends on | covers |
|---|---|---|---|
| data | packages/data | — | load trades, clean trades, store trades |
| analysis | packages/analysis | data | rolling VWAP, summary report |

## Toolchain

```
uv run pytest packages/<pkg>
# lint and format
uv run ruff check
```
"""

CONTRACT = """# data — package contract

## Purpose

Loads, cleans and stores the trade export.

## Sections

| section | responsibility | path | owner doc | builds with | depends on | source |
|---|---|---|---|---|---|---|
| ingest | read the export | packages/data/src/data/ingest/ | docs/packages/data/design/ingest.md | csv | — | {source} |
| clean | dedupe and sort | packages/data/src/data/clean/ | docs/packages/data/design/clean.md | — | ingest | — |
| storage | persist to SQLite | packages/data/src/data/storage/ | docs/packages/data/design/storage.md | sqlite3 | clean | — |
| surface | the package's pipelines (§4) and public surface (§6) | packages/data/src/data/ | docs/packages/data/design/surface.md | — | ingest, clean, storage | — |

## Public surface (intent)

- `load_trades`, realized by ingest, consumed by analysis
"""

# The `call_paths: true` body of `base` (2.6, phase 3): the `commands` macro's tree as a
# **Call paths** entry, so a contract can match the code `--paths` reads.
CALL_PATHS = """- `data-load` (budget 8):
  - file write: 1 `cli.load` → 2 `pipelines.run_load` → 3 `ingest.read_trades` → `shutil.copy`
"""

# The `stage: true` option of `base` (2.7, phase 2): the `clean` row marked as a data stage.
STAGE_ROW = ("| clean | dedupe and sort | packages/data/src/data/clean/ | docs/packages/data/design/clean.md | — | ingest | — |",
             "| clean | dedupe and sort | packages/data/src/data/clean/ | docs/packages/data/design/clean.md | dev-team:data-quality | ingest | stage:rawtrades |")
STAGE_CONVENTIONS = """
## Package conventions

- `stage:rawtrades` — the trade rows ingest reads; lands at data/trades.csv; pull cap 400 rows, D1
"""

# The `profile` macro's document (2.7, phase 2): a round-0 data profile, before its round lines.
PROFILE = """# Source probe — rawtrades — stage — 2026-09-27

Purpose: dedupe and sort
Profile: rawtrades.profile.py · Examples: rawtrades.sample.json

## Quirks

- K1 exact duplicates — checks C1; 2 of 400; the same row twice; proposed: drop; D?; unverified

## Sections served

## data/{section}

dedupe and sort
"""

TRADES = """# trades — dataset

## Kind `dataset`

`data/trades.csv`, 400 rows.

## Quirks

- two exact duplicate rows

## data/ingest

- columns `ts`, `symbol`, `price`, `size`, `side`
"""

POLYGON = """# polygon — api

## Kind `api`

## Access

- env `POLYGON_API_KEY`
"""

README = """# {section}

## Purpose

The {section} section.

## Files

- `__init__.py`

## Entry points and interfaces

| name | signature | one-line use case | Public |
|---|---|---|---|
| `{name}` | `{name}(path)` | {section} the trades | {public} |

## Pipeline / workflow

- one step

## Configuration

- none

## Running and testing

- `uv run pytest packages/data`

## Implementation notes

- none
"""

INTERFACE = """# data — interface

## Public names

| name | kind | signature | providing module | consumer | since |
|---|---|---|---|---|---|
| load_trades | function | load_trades(path) | data.ingest | analysis | 2026-09-27 |

## Pipelines

- none

## CLI commands

- none

## Configuration

- none

## Shapes provided

- Trade

## Deviations

- none

## Consumers (computed)

- analysis
"""

SURFACE_INIT = '''"""data — the public surface."""

__all__ = ["load_trades"]


def __getattr__(name):
    if name == "load_trades":
        from data.ingest import load_trades

        return load_trades
    raise AttributeError(name)
'''

ENTRY = {"ingest": ("load_trades", "yes"), "clean": ("dedupe", "no"), "storage": ("store", "no")}

# The `commands` macro's package (2.5, phase 4): one command whose call tree reaches two
# effects at depth 2, the block `calltree-direct` expects line for line.
COMMANDS = {
    "packages/data/pyproject.toml": """[project]
name = "data"
version = "0.0.0"

[project.scripts]
data-load = "data.cli:load"
""",
    "packages/data/src/data/cli.py": '''"""Commands."""

from data.pipelines.load import run_load


def load(path: str) -> None:
    """Load the trades at path."""
    run_load(path)
''',
    "packages/data/src/data/pipelines/__init__.py": "",
    "packages/data/src/data/pipelines/load.py": '''"""The load pipeline."""

from data.ingest.reader import read_trades


def run_load(path: str) -> int:
    """Read the trades at path and return their count."""
    # Read the file into rows.
    rows = read_trades(path)
    return len(rows)
''',
    "packages/data/src/data/ingest/reader.py": '''"""Read trades."""

import csv
import shutil


def read_trades(path: str) -> list[dict[str, str]]:
    """Copy path to a scratch file and parse the copy."""
    shutil.copy(path, path + ".bak")
    with open(path + ".bak") as handle:
        return list(csv.DictReader(handle))
''',
}


def run(dest: Path, *args: str) -> str:
    out = subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                          "-c", "commit.gpgsign=false", *args], cwd=dest, capture_output=True, text=True)
    if out.returncode != 0:
        raise SystemExit(f"git {' '.join(args)} failed: {out.stderr}")
    return out.stdout.strip()


def write(dest: Path, files: dict[str, str]) -> None:
    head = run(dest, "rev-parse", "HEAD")
    for rel, content in files.items():
        p = dest / rel
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(content.replace("{HEAD}", head))


def commit(dest: Path, files: dict[str, str], message: str) -> None:
    write(dest, files)
    run(dest, "add", "--", *files)
    run(dest, "commit", "-q", "-m", message, "--", *files)


def append(dest: Path, rel: str, text: str) -> dict[str, str]:
    return {rel: (dest / rel).read_text() + text}


# Macros: each returns a list of (files, message) commits.


def m_base(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    files = {"docs/architecture.md": ARCHITECTURE}
    contract = step.get("contract", "dataset")
    if contract:
        text = CONTRACT.format(source="api:polygon" if contract == "api" else "dataset:trades")
        if step.get("shorthand"):  # path cells as `…/<name>/`, the shorthand a preamble explains
            text = text.replace("| packages/data/src/data/ingest/ |", "| …/ingest/ |")
        cp = step.get("call_paths", False)
        if cp:
            body = CALL_PATHS if cp is True else cp
            text += "\n## Call paths\n\n" + body.rstrip("\n") + "\n"
        if step.get("stage"):
            text = text.replace(*STAGE_ROW) + STAGE_CONVENTIONS
        files["docs/packages/data/contract.md"] = text
    if step.get("sources", True):
        if contract == "api":
            files["docs/sources/polygon.md"] = POLYGON
        else:
            files["docs/sources/trades.md"] = TRADES
    return [(files, "docs: architecture, data contract, probe doc")]


def m_profile(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    """`docs/sources/rawtrades.md` with one round line per entry of `lines`; `append` adds only the lines."""
    rel = "docs/sources/rawtrades.md"
    out = []
    for entry in step.get("lines", []):
        e = {"round": 0, "commit": "none", "verdict": entry} if isinstance(entry, str) else entry
        out.append(f"Round {e['round']} — {DATE} — commit {e['commit']} — {e['verdict']}\n")
    if step.get("append"):
        text = (dest / rel).read_text() + "".join(out)
    else:
        text = PROFILE.format(section=step.get("section", "clean")) + ("\n" + "".join(out) if out else "")
    return [({rel: text}, "docs/sources: rawtrades profiled")]


def m_design(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s = step["section"]
    text = f"# {PKG}/{s} — design\nMode: new\n\n## 5. Interfaces\n\n- the {s} entry point\n"
    return [({f"docs/packages/{PKG}/design/{s}.md": text}, f"{PKG}/{s}: design")]


def m_tests(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s = step["section"]
    name = ENTRY.get(s, ("load_trades", ""))[0]
    text = f'def test_{s}():\n    """Design §5 {name}: the entry point answers."""\n    assert True\n'
    return [({f"packages/{PKG}/tests/intent/{s}/test_{s}.py": text}, f"{PKG}/{s}: intent tests")]


def m_build(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s = step["section"]
    unit = {f"packages/{PKG}/tests/unit/{s}/test_unit_{s}.py": f"def test_unit_{s}():\n    assert True\n"}
    if s == "surface":
        files = {f"packages/{PKG}/src/{PKG}/__init__.py": SURFACE_INIT,
                 f"docs/packages/{PKG}/interface.md": INTERFACE, **unit}
    else:
        name, public = ENTRY[s]
        files = {f"packages/{PKG}/src/{PKG}/{s}/__init__.py": f'"""{s}."""\n\n\ndef {name}(path):\n    return []\n',
                 f"packages/{PKG}/src/{PKG}/{s}/README.md": README.format(section=s, name=name, public=public), **unit}
    return [(files, f"{PKG}/{s}: build")]


def m_commands(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    """The five files of a package with one command, `files` replacing or adding any of them."""
    return [({**COMMANDS, **step.get("files", {})}, f"{PKG}/surface: commands")]


def m_review(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s, n = step["section"], step.get("round", 1)
    files = {}
    for suffix, verdict in step["reports"].items():
        focus = {"a": "conformance", "b": "correctness", "s": "full"}[suffix]
        head = [f"# Review — {PKG}/{s} — round {n} — {focus}", "Scope: design, contract, code", "Commit: {HEAD}",
                f"Verdict: {verdict}", f"Round: {n}", f"Focus: {focus}"]
        if n > 1:
            head += [f"Convergence: {step.get('convergence', '0 prior unfixed, 0 new')}", "Diff: {HEAD}..HEAD"]
        body = "\n\n## CRITICAL\n\n" + ("- none" if verdict == "approve" else f"- src:1 — finding — fix it") + "\n\n## WARNING\n\n- none\n"
        body += "\n## Spec-change\n\n" + (f"- {step['spec'][suffix]}\n" if suffix in step.get("spec", {}) else "- none\n")
        rel = (f"docs/reviews/{DATE}-{PKG}-{s}-r{n}-{suffix}.md" if step.get("layout", "new") == "old"
               else f"docs/packages/{PKG}/reviews/{s}/{DATE}-r{n}-{suffix}.md")
        files[rel] = "\n".join(head) + body
    return [(files, f"{PKG}/{s}: review r{n}")]


def m_paths_review(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    """A paths report, `Commit:` the newest commit touching the package's code, tests or interface."""
    n, verdict = step.get("round", 1), step["verdict"]
    critical = step.get("critical", [])
    sha = run(dest, "log", "-1", "--format=%h", "--", f"packages/{PKG}/src", f"packages/{PKG}/tests",
              f"docs/packages/{PKG}/interface.md") or "none"
    head = [f"# Review — {PKG} paths — round {n}", f"Scope: every command of {PKG}", f"Commit: {sha}",
            f"Verdict: {verdict}", f"Round: {n}", f"Focus: {step.get('focus', 'paths')}"]
    body = "\n\n## CRITICAL\n\n" + ("\n".join(f"- {c}" for c in critical) or "- none") + "\n\n## WARNING\n\n- none\n"
    rel = f"docs/packages/{PKG}/reviews/paths/{DATE}-r{n}-p.md"
    return [({rel: "\n".join(head) + body}, f"review {PKG}/paths: r{n}-p: {verdict} ({len(critical)} critical)")]


def m_done(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s = {"section": step["section"]}
    return [*m_design(dest, s), *m_tests(dest, s), *m_build(dest, s),
            *m_review(dest, {**s, "reports": {"a": "approve", "b": "approve"}})]


def m_fix(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s = step["section"]
    rel = f"packages/{PKG}/src/{PKG}/{s}/__init__.py"
    return [(append(dest, rel, f"\n# {step.get('note', 'fix')}\n"), f"{PKG}/{s}: {step.get('note', 'fix')}")]


def m_edit(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    text = (dest / step["path"]).read_text()
    if "replace" in step:  # ["<old>", "<new>"], applied before `append`
        old, new = step["replace"]
        if old not in text:
            sys.exit(f"edit: {step['path']} has no {old!r} to replace")
        text = text.replace(old, new, 1)
    return [({step["path"]: text + step.get("append", "")}, step["message"])]


def m_regenerate(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s = step["section"]
    rel = f"packages/{PKG}/tests/intent/{s}/test_{s}.py"
    text = (dest / rel).read_text().replace(": the entry point answers.", f": the entry point answers (deviation {PKG}/{s} — {DATE}).")
    return [({rel: text}, f"{PKG}/{s}: regenerate 1 intent tests")]


def m_deviation(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s, kind = step["section"], step["kind"]
    new = step.get("layout", "new") == "new" and not step.get("legacy")
    rel = ("docs/deviations.md" if step.get("legacy") else
           f"docs/packages/{PKG}/deviations/{s}.md" if new else f"docs/deviations/{PKG}/{s}.md")
    old = (dest / rel).read_text() if (dest / rel).exists() else ("# Deviations\n" if step.get("legacy") else f"# Deviations — {PKG}/{s}\n")
    k = f" — {old.count(chr(10) + '## ') + 1}" if new else ""
    evidence = "Did: built it the other way" if kind == "deviation" else "Found: src/x.py:1"
    entry = (f"\n## {PKG}/{s} — {DATE} — {kind}{k}\n\nClause: {step.get('clause', 'design §5 load_trades')}\n"
             f"Said: \"one thing\"\n{evidence}\nWhy: the data says otherwise\nStatus: {step['status']}\n"
             f"Raised by: implementer — run-package {PKG}\nResolved by: —\n")
    return [({rel: old + entry}, f"{PKG}/{s}: {kind} {step['status']}")]


def m_change(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    slug = step["slug"]
    pkg = step.get("pkg", PKG)
    rel = f"docs/changes/{slug}.md" if step.get("layout", "new") == "old" else f"docs/packages/{pkg}/changes/{slug}.md"
    affected = "\n".join(f"   - {sec} — changes" for sec in step["sections"])
    text = (f"# `{rel}`\nStatus: {step.get('status', 'open')}\n\n1. **Change goal** — let the window be set per call.\n"
            f"2. **Affected sections**\n{affected}\n3. **Contract changes** — none yet\n4. **Downstream impact** — none\n")
    return [({rel: text}, f"docs: change {slug}")]


def m_inbox(dest: Path, step: dict) -> list[tuple[dict[str, str], str]]:
    s = step["section"]
    rel = f"docs/packages/{PKG}/decisions/{s}.md"
    text = f"# Decisions — {PKG}/{s}\n\n" + "\n\n".join(e.strip() for e in step["entries"]) + "\n"
    return [({rel: text}, f"{PKG}/{s}: decisions inbox")]


def apply(dest: Path, step: dict) -> None:
    if "do" in step:
        commits = globals()[f"m_{step['do']}"](dest, step)
    else:
        commits = [(step["files"], step["message"])]
    for files, message in commits:
        commit(dest, files, message)


def build(case: Path, dest: Path) -> Path:
    spec = json.loads((case / "case.json").read_text())
    if dest.exists():
        raise SystemExit(f"{dest} already exists")
    (dest / "docs").mkdir(parents=True)
    (dest / "data").mkdir()
    shutil.copy(TWO_PACKAGE / "docs" / "brief.md", dest / "docs")
    shutil.copy(TWO_PACKAGE / "data" / "trades.csv", dest / "data")
    run(dest, "init", "-q", "-b", "main")
    run(dest, "commit", "-q", "--allow-empty", "-m", "root")
    if spec.get("branch", "build") != "main":
        run(dest, "checkout", "-q", "-b", spec.get("branch", "build"))
    commit(dest, {"docs/brief.md": (dest / "docs/brief.md").read_text(),
                  "data/trades.csv": (dest / "data/trades.csv").read_text()}, "fixture: brief and trades dataset")
    for step in spec.get("steps", []):
        apply(dest, step)
    write(dest, spec.get("dirty", {}))
    if "gate" in spec:
        write_gate(dest, spec["gate"])
    return dest


def write_gate(dest: Path, records: dict[str, str]) -> None:
    """Write each section's stop-gate record to `.dev-team/gate/data/<section>.txt`, `{SECTION}`
    the short sha of the newest commit touching its code and unit tree, and exclude `.dev-team/`
    from git as a scaffolded repo's `.gitignore` would."""
    for section, text in records.items():
        sha = run(dest, "log", "-1", "--format=%H", "--", f"packages/{PKG}/src/{PKG}/{section}",
                  f"packages/{PKG}/tests/unit/{section}")
        p = dest / ".dev-team" / "gate" / PKG / f"{section}.txt"
        p.parent.mkdir(parents=True, exist_ok=True)
        p.write_text(text.replace("{SECTION}", sha[:7]))
    exclude = dest / ".git" / "info" / "exclude"
    exclude.parent.mkdir(parents=True, exist_ok=True)
    exclude.write_text((exclude.read_text() if exclude.exists() else "") + ".dev-team/\n")


def main() -> int:
    if len(sys.argv) != 3:
        print(__doc__.split("\n\n")[1])
        return 2
    case = Path(sys.argv[1])
    if not (case / "case.json").exists():
        case = HERE / sys.argv[1]
    print(build(case, Path(sys.argv[2]).resolve()))
    return 0


if __name__ == "__main__":
    sys.exit(main())
