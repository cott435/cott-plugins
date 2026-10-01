#!/usr/bin/env python3
"""Derive where every package and section stands from docs/ and the code. Nothing is stored.

Usage:  python3 status.py [pkg] [--run-gate [pkg]] [--rounds <pkg>/<section>] [--surface <pkg>] [--repo]
                          [--inputs <pkg>/<section>] [--fields <pkg>/<section>] [--scaffold <pkg>]

A section is in exactly one state, decided in this order, first match wins:

1. **BLOCKED** — an open decision with no assumption binds the section (`docs/decisions.md`
   entry with `Status: open`, no `Assumption if unanswered:`, `Scope:` covering `repo`, the
   package or the section); or the newest review round says `request changes` and the cap is
   hit: round 3 or later, or round 2 whose `Convergence:` line has one or more prior unfixed;
   or the section has a README, no review round covers its code, and the stop gate's record
   for its current commit ends `result: blocked` or `result: letting the run stop after 3
   attempts …`.
2. **PLAN** — an open `spec-change:contract` names the section.
3. **PROBE** — a source in the row's `source` column needs probing: an `api:` source whose
   `docs/sources/<token>.md` lacks a `## <pkg>/<section>` heading, or a `dataset:` source with
   no `docs/sources/<token>.md` at all.
4. **DESIGN** — no design at `docs/packages/<pkg>/design/<section>.md`; or an open
   `spec-change:design` entry; or an open change file whose **Affected sections**
   names the section and is newer than the design; or a probe doc the row names lost or
   reworded a line the design was written against (added lines, the title line and other
   sections' entries do not count).
5. **TEST** — no `tests/intent/<section>/` under the package root; or the design is newer than
   the intent tree; or an open `spec-change:test` entry; or an `approved` deviation entry whose
   `Clause:` is cited by an intent test docstring that carries no `(deviation ` tag
   (regenerate).
6. **IMPLEMENT** — no README (`<section path>/README.md`; for `surface`,
   `docs/packages/<pkg>/interface.md`); or the intent tree, regeneration and `intent tests current with design`
   commits skipped, is newer than the README; or the section has a README, no review round
   covers its code, and the gate's record for its current commit ends `result: not done
   (attempt <n> of 3)`, a run that died between attempts.
7. **REVIEW** — no review round; or round 1 lacks its `a` or `b` report; or the section's code
   (its path, `tests/unit/<section>`, `tests/intent/<section>` less those same commits, its
   README) is newer than the newest round's `Commit:`; or the newest round's verdict is
   `spec-change` with no open spec-change left.
8. **FIX n** — the newest round `n` says `request changes`, the cap is not hit, and the code is
   not newer than its `Commit:`.
9. **DONE** — the newest round approves and the code is not newer than its `Commit:`.

The **ledger** is one file per section, `docs/deviations/<pkg>/<section>.md`, so agents that
run in parallel on different sections never write the same file; a `docs/deviations.md` from
before that split is still read, and an entry moved out of it into its section's file keeps
the commit that first added it, so a move answers nothing and re-opens nothing.

Since 2.2 the section's ledger is `docs/packages/<pkg>/deviations/<section>.md`; the 2.0
location `docs/deviations/<pkg>/<section>.md` and the pre-2.0 `docs/deviations.md` are still
read, and an entry is edited in the file that holds it. Review reports are
`docs/packages/<pkg>/reviews/<section>/<date>-r<n>-<a|b|s>.md`; the 2.0 names
`docs/reviews/<date>-<pkg>-<section>-r<n>-<letter>.md` are still read as round `n`. Change
files are `docs/packages/<pkg>/changes/<slug>.md`, one per affected package; a
`docs/changes/<slug>.md` is still read as naming every package its **Affected sections**
name. A ledger heading may end `— <k>`, the entry's 1-based sequence in its file; a heading
without it is a 2.x ledger and `k` is absent. The **inbox** is
`docs/packages/<pkg>/decisions/<section>.md`: `## D? — <question>` stubs and `## D<n>` entries
holding `Applied:` lines, merged into `docs/decisions.md` by `hooks/sync_decisions.py`. This
script never writes it; `--run-gate` fails on an inbox holding anything the central ledger
does not, and on a central `Applied: <pkg>/<section>, …` line the section's inbox entry for
that `D<n>` no longer holds (the hook mirrors a section's own lines).

An **open spec-change** is a ledger entry `spec-change:<level>` with `Status: open`, or a
review report of the newest round whose verdict is `spec-change`. A ledger entry whose heading
ends `— <k>` (written by 2.2 or later) is open until the agent that answers it sets its
`Status:` to `resolved` — the tester for `test`, the designer for `design`, the architect for
`contract` — and is never closed by commit order. A ledger entry without `— <k>`, and each
level a report's **Spec-change** heading names, keep the older rule: open until the document
the level names (the design, the intent tree, the package contract) is committed after it, or,
for a report's, until a ledger entry of that level for the section is committed with or after
the report (then the entry speaks). So a round-1 `b` reviewer, which never writes the ledger,
still re-opens the step. An older `spec-change:contract` ledger entry is closed by the
architect only.

Round 1 is a pair: a round whose reports carry letters and lack `a` or `b` is REVIEW (rule 7)
whatever the other says, so one reviewer's approval never ships a section alone.

A Sections `path` cell written as `…/<name>/` (or `.../<name>/`) is the default
`<package root>/src/<pkg>/<name>/`, the shorthand a contract's preamble explains.

Ready: a section whose state is neither DONE nor BLOCKED and whose every in-package `depends
on` is DONE. The `surface` row depends on every other row whatever its cell says.
Shipped: the `surface` section is DONE. Rounds: the highest `n` over the section's review
reports, at either location; a round's verdict is the worst of its
reports (request changes > spec-change > approve); a report with no `-r<n>-` is round 1.
`--rounds <pkg>/<section>` prints a third line, `commit: <short sha>`, the newest commit
touching the section's path, `tests/unit/<section>`, `tests/intent/<section>` and its README,
or `commit: none` — the reviewer copies it as its report's `Commit:` (F12).

**Evidence.** The strings the driver copies out of a row's evidence cell:

1. **open** — `open <heading>; <heading>; …`: every open spec-change of the level that won
   the row (PLAN, DESIGN or TEST), ledger headings and `<report path> — spec-change:<level>`
   alike, `; `-separated.
2. **regenerate** — `regenerate: <heading>`: an approved deviation whose clause an untagged
   intent test cites.
3. **gate blocked** — `gate blocked: <the marker's reason>`.
4. **gate let through** — `gate let through after 3 attempts, <k> failures`.
5. **gate not done** — `gate not done (attempt <n> of 3)`.

**Gate record.** `.dev-team/gate/<pkg>/<section>.txt`, written by `hooks/gate_on_stop.py` on
every implementer stop. It speaks for the commit its `commit:` line names: the newest commit
touching the section's code, `tests/unit/<section>` and its README, the intent tree left out.
A record whose `commit:` is not that commit, a record with no `commit:` line (written before
2.4), a missing record, and a record read while those paths have uncommitted changes are all
treated as absent, and the row is derived without it. A record whose header slot is `report`
(`/dev-team:pair`'s wrap-up) or `spec-change` never holds a row. Once a review round's
`Commit:` covers the code the review speaks and the record is not read, which is what makes
the user's *review anyway* stick.

**Scaffold.** A package is ready to be built in when its workspace exists: a root
`pyproject.toml`, and, when that root is a uv workspace (`[tool.uv.workspace]`), a
`pyproject.toml` at the package root. `--scaffold <pkg>` prints `scaffold: done` and exits 0,
or `scaffold: needed (<reasons>)` and exits 1: `no root pyproject.toml`, `no <package
root>/pyproject.toml`. A root `pyproject.toml` that is not a uv workspace is an adopted repo's
own layout and needs nothing. The package block prints the same `scaffold: needed` line, before
`shipped:`, when it applies. run-package runs the SCAFFOLD step on it before any other spawn,
so every tester runs inside the workspace, under the repo's own lint rules.

`--inputs <pkg>/<section>` prints the implementer's spawn block, the one place its values are
resolved: run-package sends it verbatim as the implementer's prompt, and pair reads the files
it names before touching the section. One `<Field>: <value>` line per field, in this order,
`none` for a field with nothing to hold:

1. **Section** — `<pkg>/<section>`.
2. **Design** — `docs/packages/<pkg>/design/<section>.md`.
3. **Contract** — `docs/packages/<pkg>/contract.md`.
4. **Repo contract** — `docs/architecture.md`.
5. **Dependency READMEs** — `<path>/README.md` per section in the row's `depends on`.
6. **Upstream interfaces** — per package in the Packages row's `depends on`,
   `docs/packages/<dep>/interface.md` when it exists, else `provisional:
   docs/packages/<dep>/contract.md`.
7. **Source probes** — `docs/sources/<token>.md` per entry in the row's `source`.
8. **Intent tests** — `<package root>/tests/intent/<section>/` when it exists.
9. **Review** — from either location, the newest round's reports when its verdict is `request changes` (FIX n, or a
   cap granted one more round) or `spec-change` (a rebuild after the step it re-opened: its
   CRITICALs still stand).
10. **Round** — the newest round plus one.
11. **Change file** — from either location, every open `docs/packages/<pkg>/changes/<slug>.md`
    or `docs/changes/<slug>.md` whose Affected sections names the section.
12. **Run** — `run-package <pkg>`.

`--fields <pkg>/<section>` prints the spawn fields run-package would otherwise resolve by
reading files, four `key: value` lines in this order, and exits 0 (2 on a section the contract
lacks):

1. `mode: new | document | delta` — `delta` when an open change file names the section, or the
   state's evidence is `open <heading>` for a `spec-change:design`; `document` when the
   section's path holds a `.py` file (nested sections excluded; for `surface`, the package's
   own `__init__.py`, which the scaffold writes, does not count) and there is no design; else
   `new`. The designer's `Mode:` field.
2. `change file: <path>, … | none` — the open change files naming the section, as
   **Change file** in `--inputs`.
3. `design mode: <word> | none` — the word after `Mode:` on the design's first line (a title
   line above it is read past, up to the fifth line); `none` with no design or no such line.
   The tester's `Design mode:` field.
4. `diff base: <sha> | none` — from the newest round `n` ≥ 1, the `Commit:` of round `n`'s
   `-s` report, or its `-a` report when `n` is 1, or its one report when it has no letter;
   `none` with no round or no `Commit:`. The next reviewer's `Diff:` field is `<sha>..HEAD`.
"""

from __future__ import annotations

import ast
import json
import os
import re
import subprocess
import sys
from pathlib import Path

ROOT = Path.cwd().resolve()
DOCS = ROOT / "docs"

STATES = ("BLOCKED", "PLAN", "PROBE", "DESIGN", "TEST", "IMPLEMENT", "REVIEW", "FIX", "DONE")

# git-workflow-and-versioning §Project convention, Baseline: the files the user edits between
# runs, and agent memory, which agents write and nobody stages but the user. The one copy; a
# trailing slash exempts everything under it.
BASELINE_EXEMPT = ("docs/decisions.md", "docs/brief.md", "docs/constraints.md", ".claude/agent-memory/")

# A round's verdict is the worst of its reports; higher is worse.
VERDICT_RANK = {"approve": 0, "spec-change": 1, "request changes": 2}

UNCOMMITTED = "U"


def set_root(path: Path) -> None:
    """Point every parser at the repo rooted at path. The default is the working directory."""
    global ROOT, DOCS
    ROOT = Path(path).resolve()
    DOCS = ROOT / "docs"


# ---------------------------------------------------------------------------------------------
# Markdown parsing
# ---------------------------------------------------------------------------------------------


def table_rows(md: str, must_have: tuple[str, ...]) -> list[dict[str, str]]:
    """Return the rows of the first markdown table whose header contains every name in must_have."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        header = [c.strip().lower().strip("`* ") for c in line.strip().strip("|").split("|")]
        if all(any(m in h for h in header) for m in must_have) and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip().strip("|").split("|")]
                rows.append({h: (cells[k] if k < len(cells) else "") for k, h in enumerate(header)})
            return rows
    return []


def col(row: dict[str, str], name: str) -> str:
    """Fetch a cell by a loose header match, stripping backticks."""
    for h, v in row.items():
        if name in h:
            return v.strip("`* ")
    return ""


def _names(cell: str) -> list[str]:
    """A comma-separated cell as bare names; `—`, `-` and empty give none."""
    out = []
    for part in cell.split(","):
        name = part.strip().strip("`*_ ")
        if name and name not in ("—", "-", "–", "none"):
            out.append(name)
    return out


def _block(text: str, heading: str) -> str:
    """The body under a `##` heading named heading, up to the next `##` heading; empty when absent."""
    m = re.search(rf"^##\s+(?:\d+\.\s*)?{re.escape(heading)}\b.*?$(.*?)(?=^##\s|\Z)", text, re.M | re.S)
    return m.group(1) if m else ""


def _item(text: str, name: str) -> str:
    """The body of a heading or a numbered bold item named name, up to the next of either.

    Lines inside fenced code blocks never end the body, so a `# comment` in a shell block does
    not read as a heading.
    """
    lines = text.splitlines()
    start = None
    for i, line in enumerate(lines):
        if re.match(rf"\s*(#+\s*(\d+\.\s*)?{re.escape(name)}\b|(\d+\.\s*)?\*\*{re.escape(name)}\*\*)", line):
            start = i
            break
    if start is None:
        return ""
    body = [re.sub(rf"^.*?\*\*{re.escape(name)}\*\*\s*[—:-]?", "", lines[start])]
    fenced = False
    for line in lines[start + 1:]:
        if line.strip().startswith("```"):
            fenced = not fenced
        elif not fenced and re.match(r"\s*(#+\s|\d+\.\s*\*\*)", line):
            break
        body.append(line)
    return "\n".join(body)


def _field(text: str, key: str) -> str:
    """The value of a `Key: value` line (bold, bulleted or numbered forms accepted); empty when absent."""
    m = re.search(rf"^[ \t]*(?:[-*][ \t]+|\d+\.[ \t]+)?\**{re.escape(key)}\**[ \t]*(?::|—)\**[ \t]*(.*)$", text, re.M | re.I)
    return m.group(1).strip() if m else ""


# ---------------------------------------------------------------------------------------------
# git
# ---------------------------------------------------------------------------------------------


def git(*args: str) -> str | None:
    """Run a git command in the repo root; its stripped stdout, or None when git fails."""
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    except OSError:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def _rel(path: Path | str) -> str:
    """A path as git sees it: relative to the root, posix; pathspec magic passed through."""
    s = str(path)
    if s.startswith(":("):
        return s
    p = Path(path)
    if p.is_absolute():
        try:
            p = p.relative_to(ROOT)
        except ValueError:
            return p.as_posix()
    return p.as_posix() or "."


def last_commit(*paths: Path | str) -> str | None:
    """Full SHA of the newest commit touching any of paths; None when not a repo or none does."""
    return git("log", "-1", "--format=%H", "--", *map(_rel, paths)) or None


def uncommitted(*paths: Path | str) -> bool:
    """True when any of paths has staged, unstaged or untracked changes."""
    return bool(git("status", "--porcelain", "--untracked-files=all", "--", *map(_rel, paths)))


def _is_regen(summary: str, pkg: str, section: str) -> bool:
    return re.match(rf"{re.escape(pkg)}/{re.escape(section)}: (regenerate \d+ intent tests|intent tests current with design)", summary) is not None


def _log(paths: tuple[Path | str, ...], since: str | None = None) -> list[tuple[str, str]]:
    """(sha, summary) of every commit touching paths, newest first; only after since when given."""
    rng = [f"{since}..HEAD"] if since else []
    out = git("log", "--format=%H%x1f%s", *rng, "--", *map(_rel, paths)) or ""
    return [tuple(line.split("\x1f", 1)) for line in out.splitlines() if "\x1f" in line]  # type: ignore[misc]


def changed_since(sha: str, *paths: Path | str, skip_regen: tuple[str, str] | None = None) -> str | None:
    """The first commit after sha touching paths ('U' for uncommitted changes), or None.

    sha not in this history counts as changed: its sha is returned. With skip_regen=(pkg,
    section), commits whose summary is that section's `regenerate <k> intent tests` or `intent
    tests current with design` are skipped.
    """
    if uncommitted(*paths):
        return UNCOMMITTED
    if git("merge-base", "--is-ancestor", sha, "HEAD") is None:
        return sha
    for c, summary in reversed(_log(paths, since=sha)):
        if not (skip_regen and _is_regen(summary, *skip_regen)):
            return c
    return None


def _rev(*paths: Path | str, skip_regen: tuple[str, str] | None = None) -> str | None:
    """'U' when any path is uncommitted, else the newest commit touching them, else None."""
    if uncommitted(*paths):
        return UNCOMMITTED
    for c, summary in _log(paths):
        if not (skip_regen and _is_regen(summary, *skip_regen)):
            return c
    return None


def _newer(b: str | None, a: str | None) -> bool:
    """True when revision b is newer than revision a, by commit order ('U' is newest of all)."""
    if b is None or b == a:
        return False
    if b == UNCOMMITTED:
        return True
    if a == UNCOMMITTED:
        return False
    if a is None:
        return True
    return git("merge-base", "--is-ancestor", a, b) is not None


def _short(rev: str | None) -> str:
    return "uncommitted" if rev == UNCOMMITTED else rev[:7] if rev else "—"


# ---------------------------------------------------------------------------------------------
# Packages and sections
# ---------------------------------------------------------------------------------------------


def packages() -> list[tuple[str, Path]]:
    """(name, path) for every row of architecture.md's Packages table; docs/packages/* without one."""
    arch = DOCS / "architecture.md"
    out: list[tuple[str, Path]] = []
    if arch.exists():
        for row in table_rows(arch.read_text(), ("package", "path")):
            name, path = col(row, "package"), col(row, "path")
            if name and not name.startswith("-"):
                out.append((name, (ROOT / (path or ".")).resolve()))
    if not out and (DOCS / "packages").is_dir():
        out = [(d.name, ROOT / "packages" / d.name) for d in sorted((DOCS / "packages").glob("*")) if d.is_dir()]
    return out


def package_root(pkg: str) -> Path:
    """packages/<pkg>, or the path the Packages table gives it (the root for `.`)."""
    for name, path in packages():
        if name == pkg:
            return path
    return ROOT / "packages" / pkg


def contract_path(pkg: str) -> Path:
    return DOCS / "packages" / pkg / "contract.md"


def sections(pkg: str) -> list[dict[str, str]]:
    """The Sections table rows of the package contract, path resolved relative to the root.

    Keys: section, responsibility, path, owner doc, builds with, depends on, source. The
    `surface` row's `depends on` is every other section, whatever its cell says.
    """
    f = contract_path(pkg)
    if not f.exists():
        return []
    root = package_root(pkg)
    out = []
    for row in table_rows(f.read_text(), ("section", "path")):
        name = col(row, "section")
        if not name or name.startswith("-"):
            continue
        cell = col(row, "path")
        default = root / "src" / pkg / ("" if name == "surface" else name)
        short = re.fullmatch(r"(?:…|\.\.\.)/([\w.-]+)/?", cell or "")
        path = default.parent / short.group(1) if short else (ROOT / cell) if cell and cell not in ("—", "-") else default
        out.append({
            "section": name,
            "responsibility": col(row, "responsibility"),
            "path": _rel(path.resolve()).rstrip("/"),
            "owner doc": col(row, "owner"),
            "builds with": col(row, "builds"),
            "depends on": col(row, "depends"),
            "source": col(row, "source"),
        })
    names = [r["section"] for r in out]
    for r in out:
        if r["section"] == "surface":
            r["depends on"] = ", ".join(n for n in names if n != "surface")
    return out


def _row(pkg: str, section: str) -> dict[str, str] | None:
    return next((r for r in sections(pkg) if r["section"] == section), None)


def section_for_path(path: Path) -> tuple[str, str] | None:
    """(pkg, section) by longest section path prefix; the package top level → (pkg, "surface").

    A file under `<package root>/tests/intent/<section>/` or `tests/unit/<section>/` belongs to
    that section too.
    """
    p = Path(path)
    rel = _rel(p if p.is_absolute() else (ROOT / p).resolve())
    best: tuple[int, str, str] | None = None
    for pkg, root in packages():
        proot = _rel(root)
        for r in sections(pkg):
            prefixes = [r["path"]]
            for tree in ("intent", "unit"):
                prefixes.append(f"{proot}/tests/{tree}/{r['section']}" if proot != "." else f"tests/{tree}/{r['section']}")
            for pre in prefixes:
                if rel == pre or rel.startswith(pre.rstrip("/") + "/"):
                    if best is None or len(pre) > best[0]:
                        best = (len(pre), pkg, r["section"])
    return (best[1], best[2]) if best else None


def _paths(pkg: str, section: str) -> dict[str, object]:
    """Every path the state rules read for one section."""
    row = _row(pkg, section) or {"path": _rel(package_root(pkg) / "src" / pkg / section), "source": ""}
    root = package_root(pkg)
    spath = row["path"]
    nested = [r["path"] for r in sections(pkg) if r["section"] != section and r["path"].startswith(spath.rstrip("/") + "/")]
    code = [spath, *(f":(exclude){n}" for n in nested)]
    readme = (DOCS / "packages" / pkg / "interface.md") if section == "surface" else (ROOT / spath / "README.md")
    return {
        "row": row,
        "design": DOCS / "packages" / pkg / "design" / f"{section}.md",
        "intent": root / "tests" / "intent" / section,
        "unit": root / "tests" / "unit" / section,
        "code": code,
        "readme": readme,
    }


# ---------------------------------------------------------------------------------------------
# Ledgers: decisions, deviations, changes, reviews
# ---------------------------------------------------------------------------------------------


def _no_assumption(value: str) -> bool:
    return value.strip().strip("`*_ ").lower() in ("", "none", "—", "-", "–")


def decisions() -> list[dict[str, str]]:
    """Every `## D<n> — <question>` entry: n, question, scope, status, assumption."""
    f = DOCS / "decisions.md"
    if not f.exists():
        return []
    out = []
    for e in re.split(r"^## D(?=\d)", f.read_text(), flags=re.M)[1:]:
        head = e.splitlines()[0] if e.strip() else ""
        m = re.match(r"(\d+)\s*[—–-]?\s*(.*)", head)
        if not m:
            continue
        out.append({
            "n": m.group(1),
            "question": m.group(2).strip(),
            "scope": _field(e, "Scope") or _field(e, "Sections"),
            "status": _field(e, "Status").lower(),
            "assumption": _field(e, "Assumption if unanswered"),
        })
    return out


def _binds(scope: str, pkg: str, section: str) -> bool:
    for t in _names(scope):
        if t in ("repo", pkg, f"{pkg}/{section}") or ("/" not in t and t == section):
            return True
    return False


def blocking_decisions(pkg: str, section: str) -> list[str]:
    """D<n> that are open, have no assumption, and bind repo, pkg, or pkg/section."""
    return [f"D{d['n']}" for d in decisions()
            if d["status"].startswith("open") and _no_assumption(d["assumption"]) and _binds(d["scope"], pkg, section)]


DEVIATION_FIELDS = ("Clause", "Said", "Did", "Found", "Why", "Status", "Raised by", "Resolved by")


LEGACY_LEDGER = "deviations.md"


def ledger_path(pkg: str, section: str) -> Path:
    """The section's ledger: `docs/packages/<pkg>/deviations/<section>.md`."""
    return DOCS / "packages" / pkg / "deviations" / f"{section}.md"


def old_ledger_path(pkg: str, section: str) -> Path:
    """The 2.0 location of the section's ledger, `docs/deviations/<pkg>/<section>.md`; read only."""
    return DOCS / "deviations" / pkg / f"{section}.md"


def ledger_files(pkg: str | None = None, section: str | None = None) -> list[Path]:
    """The ledger files that can hold pkg's (and section's) entries: the pre-split
    `docs/deviations.md` when it exists, then the 2.0 per-section files, then the 2.2 ones."""
    out = [DOCS / LEGACY_LEDGER] if (DOCS / LEGACY_LEDGER).exists() else []
    if pkg and section:
        out += [f for f in (old_ledger_path(pkg, section), ledger_path(pkg, section)) if f.exists()]
    elif pkg:
        out += sorted((DOCS / "deviations" / pkg).glob("*.md")) + sorted((DOCS / "packages" / pkg / "deviations").glob("*.md"))
    else:
        out += sorted((DOCS / "deviations").glob("*/*.md")) + sorted((DOCS / "packages").glob("*/deviations/*.md"))
    return out


def inbox_path(pkg: str, section: str) -> Path:
    """The section's decisions inbox, `docs/packages/<pkg>/decisions/<section>.md`."""
    return DOCS / "packages" / pkg / "decisions" / f"{section}.md"


def inbox_files(pkg: str | None = None) -> list[Path]:
    """Every inbox of one package, or of the repo."""
    return sorted((DOCS / "packages").glob(f"{pkg or '*'}/decisions/*.md"))


def _applied_lines(body: str) -> list[str]:
    """The stripped `Applied:` lines of an entry body, bulleted or bold forms included."""
    return [line.strip() for line in body.splitlines()
            if re.match(r"(?:[-*]\s+)?\**Applied\**\s*:", line.strip())]


def applied_owner(line: str) -> str | None:
    """The `<pkg>/<section>` an `Applied:` line names first, or None."""
    m = re.match(r"(?:[-*]\s+)?\**Applied\**\s*:\s*\**\s*([\w.-]+/[\w.-]+)\s*,", line.strip())
    return m.group(1) if m else None


def inbox_section(path: Path) -> str:
    """`<pkg>/<section>` of an inbox path, `docs/packages/<pkg>/decisions/<section>.md`."""
    return f"{Path(path).parent.parent.name}/{Path(path).stem}"


def inbox_entries(path: Path) -> list[dict[str, object]]:
    """The entries of one inbox: heading, n (`?` or digits), question, Applied, Status, raw."""
    try:
        text = Path(path).read_text()
    except OSError:
        return []
    out: list[dict[str, object]] = []
    for e in re.split(r"^## (?=D[?\d])", text, flags=re.M)[1:]:
        head = e.splitlines()[0].strip()
        m = re.match(r"D(\?|\d+)\s*(?:[—–-]+\s*(.*))?$", head)
        if not m:
            continue
        out.append({"heading": head, "n": m.group(1), "question": (m.group(2) or "").strip(),
                    "Applied": _applied_lines(e), "Status": _field(e, "Status"), "raw": e})
    return out


def _central_bodies() -> dict[str, str]:
    """n → body of every `## D<n>` entry of docs/decisions.md."""
    f = DOCS / "decisions.md"
    if not f.exists():
        return {}
    out = {}
    for e in re.split(r"^## D(?=\d)", f.read_text(), flags=re.M)[1:]:
        m = re.match(r"\d+", e)
        if m:
            out.setdefault(m.group(0), e)
    return out


def unsynced_inboxes() -> list[str]:
    """One reason per inbox entry the central ledger lacks, and per central `Applied:` line of
    the inbox's own section that the inbox entry no longer holds; [] when every inbox is merged."""
    central = _central_bodies()
    out = []
    for f in inbox_files():
        own = inbox_section(f)
        for e in inbox_entries(f):
            n = str(e["n"])
            if n == "?":
                out.append(f"{_rel(f)}: D? stub not yet numbered")
            elif n not in central:
                out.append(f"{_rel(f)}: D{n} not in docs/decisions.md")
            else:
                have = {line.strip() for line in central[n].splitlines()}
                for line in e["Applied"]:  # type: ignore[union-attr]
                    if line not in have:
                        out.append(f"{_rel(f)}: D{n} Applied: line not in docs/decisions.md")
                        break
                for line in _applied_lines(central[n]):
                    if applied_owner(line) == own and line not in e["Applied"]:  # type: ignore[operator]
                        out.append(f"{_rel(f)}: stale Applied: line — D{n}: {line}")
    return out


def deviation_entries(pkg: str, section: str | None = None) -> list[dict[str, str]]:
    """Ledger entries for pkg (and section): heading fields, the eight fields, and the file.

    Keys: heading, pkg, section, date, kind, k (the heading's `— <k>`, "" on a 2.x heading),
    file, and Clause, Said, Did, Found, Why, Status, Raised by, Resolved by.
    """
    out = []
    for f in ledger_files(pkg, section):
        for e in re.split(r"^## ", f.read_text(), flags=re.M)[1:]:
            head = e.splitlines()[0].strip()
            m = re.match(r"`?([\w.-]+)/([\w.-]+)`?\s+[—–-]+\s+(\S+)\s+[—–-]+\s+`?([\w:-]+)`?(?:\s+[—–-]+\s+(\d+))?\s*$", head)
            if not m or m.group(1) != pkg or (section is not None and m.group(2) != section):
                continue
            entry = {"heading": head, "pkg": m.group(1), "section": m.group(2), "date": m.group(3),
                     "kind": m.group(4).lower(), "k": m.group(5) or "", "file": _rel(f)}
            for k in DEVIATION_FIELDS:
                entry[k] = _field(e, k)
            out.append(entry)
    return out


def _status(entry: dict[str, str]) -> str:
    return entry.get("Status", "").strip("`*_ ").lower().split()[0] if entry.get("Status", "").strip("`*_ ") else ""


def open_spec_changes(pkg: str, section: str | None = None) -> list[dict[str, str]]:
    return [e for e in deviation_entries(pkg, section) if e["kind"].startswith("spec-change") and _status(e) == "open"]


def entry_rev(entry: dict[str, str]) -> str | None:
    """The commit that added the entry (its heading to its ledger file, or its report); 'U' when
    not yet committed."""
    if entry.get("source") == "report":
        return entry["rev"]
    # Every ledger path, not only the entry's file: an entry moved between docs/deviations.md,
    # docs/deviations/ and docs/packages/*/deviations/ keeps the commit that first added it.
    heading = f"## {entry['heading']}"
    sha = (git("log", "--reverse", "--format=%H", "-S", heading, "--", "docs/deviations.md", "docs/deviations",
               "docs/packages/*/deviations/*.md") or "").split("\n")[0]
    return sha or UNCOMMITTED


def answered(entry: dict[str, str], rev: str | None) -> bool:
    """True when a spec-change is answered. A ledger entry whose heading carries `— <k>` (2.2 or
    later) speaks through its `Status:`: it is live while that reads `open`, whatever was
    committed since. An older ledger entry and a report-raised one keep the commit-order rule:
    answered when rev (the design, the intent tree, or for a report's, the contract) was
    committed after it. An older contract-level ledger entry is closed by the architect only."""
    if entry.get("source") != "report" and entry.get("k"):
        return False
    if entry["kind"] == "spec-change:contract" and entry.get("source") != "report":
        return False
    return _newer(rev, entry_rev(entry))


SPEC_LEVELS = ("contract", "design", "test")


def _spec_levels(text: str) -> list[str]:
    """The levels a report's **Spec-change** heading names, one per bullet, in order; a bullet
    naming none is `design`."""
    block = re.search(r"^#+\s*\**Spec-change\**\s*$(.*?)(?=^#+\s|\Z)", text, re.M | re.S)
    out: list[str] = []
    for line in (block.group(1) if block else "").splitlines():
        line = line.strip()
        if not line.startswith(("-", "*")) or re.fullmatch(r"[-*]\s*none\.?", line, re.I):
            continue
        m = re.search(r"spec-change:(contract|design|test)\b", line, re.I) or re.search(r"\b(contract|design|test)\b", line, re.I)
        level = m.group(1).lower() if m else "design"
        if level not in out:
            out.append(level)
    return out


def report_spec_changes(pkg: str, section: str) -> list[dict[str, str]]:
    """The spec-changes the newest round's `spec-change` reports raise that no ledger entry of the
    same level, committed with or after the report, records."""
    reps = _reports(pkg, section)
    if not reps:
        return []
    ledger = deviation_entries(pkg, section)
    out = []
    for f in sorted(reps[max(reps)]):
        if _verdict(_report_fields(f).get("Verdict")) != "spec-change":
            continue
        rev = _rev(f)
        for level in _spec_levels(f.read_text()):
            kind = f"spec-change:{level}"
            if any(e["kind"] == kind and not _newer(rev, entry_rev(e)) for e in ledger):
                continue
            out.append({"heading": f"{_rel(f)} — {kind}", "pkg": pkg, "section": section, "kind": kind,
                        "file": _rel(f), "source": "report", "rev": rev or UNCOMMITTED, "Status": "open"})
    return out


def live_spec_changes(pkg: str, section: str) -> list[dict[str, str]]:
    """Open spec-changes for one section, from the ledger and from the newest round's reports,
    that no later design, intent-tree or (for a report's) contract commit answered."""
    p = _paths(pkg, section)
    revs = {"spec-change:design": _rev(p["design"]), "spec-change:test": _rev(p["intent"]),  # type: ignore[arg-type]
            "spec-change:contract": _rev(contract_path(pkg))}
    return [e for e in [*open_spec_changes(pkg, section), *report_spec_changes(pkg, section)]
            if not answered(e, revs.get(e["kind"]))]


def clause_key(text: str) -> tuple[str, str] | None:
    """(n, item) of a `design §<n> <item>` citation, case-insensitive; None when there is none.

    The item is the whole name up to the first `:`, `;`, `,`, closing backtick or line end,
    backticks and `*` stripped, whitespace collapsed, lowercased (W3): `design §5 load trades
    from csv: one dict` → ("5", "load trades from csv").
    """
    m = re.search(r"design\s*§\s*(\d+)\s+(`?)([^:;,`\n]*)", text, re.I)
    if not m:
        return None
    item = " ".join(m.group(3).replace("*", "").split()).lower()
    return (m.group(1), item) if item else None


def change_files() -> list[dict[str, object]]:
    """Every change file: `docs/changes/<slug>.md` (pkg None), then `docs/packages/<pkg>/changes/<slug>.md`.

    Keys: slug, path, pkg, status, and the sections **Affected sections** names.
    """
    found = [(None, f) for f in sorted((DOCS / "changes").glob("*.md"))]
    found += [(f.parent.parent.name, f) for f in sorted((DOCS / "packages").glob("*/changes/*.md"))]
    out = []
    for pkg, f in found:
        text = f.read_text()
        affected = _item(text, "Affected sections")
        out.append({
            "slug": f.stem,
            "path": f,
            "pkg": pkg,
            "status": _field(text, "Status").strip("`*_ ").lower(),
            "sections": set(re.findall(r"\b([\w.-]+/[\w.-]+)\b", affected)),
        })
    return out


def open_changes(pkg: str, section: str | None = None) -> list[dict[str, object]]:
    """Open change files naming pkg (or pkg/section); a per-package file names only its own package's sections."""
    out = []
    for c in change_files():
        if not str(c["status"]).startswith("open"):
            continue
        if c["pkg"] is not None and c["pkg"] != pkg:
            continue
        secs: set[str] = c["sections"]  # type: ignore[assignment]
        if (section and f"{pkg}/{section}" in secs) or (not section and any(s.startswith(f"{pkg}/") for s in secs)):
            out.append(c)
    return out


def _reports(pkg: str, section: str) -> dict[int, list[Path]]:
    """Review reports of one section grouped by round, from `docs/packages/<pkg>/reviews/<section>/`
    and the flat `docs/reviews/`. A 0.6-era report is round 1, suffix s."""
    stem = re.escape(f"{pkg}-{section}")
    new = re.compile(rf"\d{{4}}-\d{{2}}-\d{{2}}-{stem}-r(\d+)-([abs])\.md")
    old = re.compile(rf"(\d{{4}}-\d{{2}}-\d{{2}})-{stem}(?:-(\d+))?\.md")
    per_section = re.compile(r"\d{4}-\d{2}-\d{2}-r(\d+)-([abs])\.md")
    rounds_: dict[int, list[Path]] = {}
    olds: list[tuple[str, int, Path]] = []
    for f in (DOCS / "packages" / pkg / "reviews" / section).glob("*.md"):
        if m := per_section.fullmatch(f.name):
            rounds_.setdefault(int(m.group(1)), []).append(f)
    for f in (DOCS / "reviews").glob(f"*-{pkg}-{section}*.md"):
        if m := new.fullmatch(f.name):
            rounds_.setdefault(int(m.group(1)), []).append(f)
        elif m := old.fullmatch(f.name):
            olds.append((m.group(1), int(m.group(2) or 1), f))
    if olds and 1 not in rounds_:
        # Several same-scope 0.6 reports are one loop; the newest one speaks for it.
        rounds_[1] = [max(olds)[2]]
    return rounds_


REPORT_FIELDS = ("Scope", "Commit", "Verdict", "Round", "Focus", "Convergence", "Diff")


def _report_fields(f: Path) -> dict[str, str]:
    text = f.read_text()
    out = {}
    for k in REPORT_FIELDS:
        m = re.search(rf"^\**{k}:\**\s*(.*)$", text, re.M)
        if m:
            out[k] = m.group(1).strip()
    return out


def _verdict(value: str | None) -> str:
    """A Verdict: value normalized; absent or unrecognized reads as `request changes`."""
    v = (value or "").strip("`*_ ").lower()
    if v.startswith("approve"):
        return "approve"
    if v.startswith("spec-change") or v.startswith("spec change"):
        return "spec-change"
    return "request changes"


def rounds(pkg: str, section: str) -> int:
    """The newest review round of a section; 0 with none."""
    return max(_reports(pkg, section), default=0)


def newest_round(pkg: str, section: str) -> tuple[int, str, str | None, dict[str, str]]:
    """(n, verdict, Commit sha, header fields) of the newest round; (0, "", None, {}) with none.

    The verdict is the worst of the round's reports. The Commit is the earliest over its
    reports, and None when any report lacks one. Header fields are the worst report's.
    """
    reps = _reports(pkg, section)
    if not reps:
        return 0, "", None, {}
    n = max(reps)
    parsed = [_report_fields(f) for f in sorted(reps[n])]
    worst = max(parsed, key=lambda p: VERDICT_RANK[_verdict(p.get("Verdict"))])
    shas = [re.match(r"[0-9a-f]{7,40}", p.get("Commit", "").strip("`")) for p in parsed]
    sha: str | None = None
    if all(shas):
        sha = shas[0].group(0)  # type: ignore[union-attr]
        for m in shas[1:]:
            if git("merge-base", "--is-ancestor", m.group(0), sha) is not None:  # type: ignore[union-attr]
                sha = m.group(0)  # type: ignore[union-attr]
    return n, _verdict(worst.get("Verdict")), sha, worst


def _missing_letters(pkg: str, section: str) -> list[str]:
    """Round 1's missing half: `a` or `b` when its reports carry letters and one is absent."""
    letters = {m.group(1) for f in _reports(pkg, section).get(1, [])
               if (m := re.search(r"-r1-([abs])\.md$", f.name))}
    if not letters or "s" in letters:
        return []
    return [x for x in ("a", "b") if x not in letters]


def _prior_unfixed(fields: dict[str, str]) -> int:
    m = re.search(r"(\d+)\s+prior unfixed", fields.get("Convergence", ""))
    return int(m.group(1)) if m else 0


# ---------------------------------------------------------------------------------------------
# Sources
# ---------------------------------------------------------------------------------------------


def _sources(cell: str) -> list[tuple[str, str]]:
    """(kind, token) per entry of a `source` cell; a bare token is `api`."""
    out = []
    for name in _names(cell):
        kind, _, token = name.partition(":") if ":" in name else ("api", "", name)
        out.append((kind.strip().lower(), token.strip().lower()))
    return out


def _has_section_heading(text: str, pkg: str, section: str) -> bool:
    return re.search(rf"^##\s+`?{re.escape(pkg)}/{re.escape(section)}`?\s*$", text, re.M) is not None


def _strip_other_sections(text: str, pkg: str, section: str) -> str:
    """A probe doc less every `## <pkg>/<section>` block but this section's own."""
    parts = re.split(r"(?=^##\s)", text, flags=re.M)
    keep = []
    for part in parts:
        m = re.match(r"##\s+`?([\w.-]+)/([\w.-]+)`?\s*$", part.splitlines()[0]) if part.startswith("##") else None
        if m and (m.group(1), m.group(2)) != (pkg, section):
            continue
        keep.append(part.rstrip())
    return "\n".join(keep).strip()


def _shared_lines(text: str, pkg: str, section: str) -> list[str]:
    """A probe doc's non-blank lines, less its title line (the first line starting `# `) and
    every `## <pkg>/<section>` entry but this section's own."""
    lines = [line for line in _strip_other_sections(text, pkg, section).splitlines() if line.strip()]
    title = next((i for i, line in enumerate(lines) if line.startswith("# ")), None)
    if title is not None:
        del lines[title]
    return lines


def _is_subsequence(needle: list[str], hay: list[str]) -> bool:
    """True when every item of needle appears in hay, in order."""
    it = iter(hay)
    return all(any(x == y for y in it) for x in needle)


def _probe_newer(doc: Path, design_rev: str | None, pkg: str, section: str) -> str | None:
    """The probe doc's revision when it changed the design's view of the source, else None.

    The doc as it stood at the design's commit is compared with the doc now, line by line, each
    reduced by `_shared_lines`. Added lines, the title line (its date) and other sections'
    `## <pkg>/<section>` entries re-open nothing: a new consuming section makes that section
    need PROBE, not this design stale. A design-time line that is gone or reworded does.
    """
    doc_rev = _rev(doc)
    if not _newer(doc_rev, design_rev):
        return None
    if design_rev in (None, UNCOMMITTED):
        return doc_rev
    before = git("show", f"{design_rev}:{_rel(doc)}")
    if before is None:
        return doc_rev
    now = doc.read_text() if doc.exists() else ""
    if _is_subsequence(_shared_lines(before, pkg, section), _shared_lines(now, pkg, section)):
        return None
    return doc_rev


# ---------------------------------------------------------------------------------------------
# The state
# ---------------------------------------------------------------------------------------------


def intent_docstrings(tree: Path) -> dict[str, str]:
    """Test node id → first docstring line, for every test function under tree, via ast."""
    out: dict[str, str] = {}
    if not tree.is_dir():
        return out
    for f in sorted(tree.rglob("*.py")):
        if not (f.name.startswith("test_") or f.name.endswith("_test.py")):
            continue
        try:
            mod = ast.parse(f.read_text())
        except (SyntaxError, UnicodeDecodeError):
            continue
        rel = _rel(f.resolve())

        def visit(body: list[ast.stmt], prefix: str) -> None:
            for node in body:
                if isinstance(node, (ast.FunctionDef, ast.AsyncFunctionDef)) and node.name.startswith("test"):
                    doc = ast.get_docstring(node) or ""
                    out[f"{prefix}::{node.name}"] = doc.strip().splitlines()[0] if doc.strip() else ""
                elif isinstance(node, ast.ClassDef) and node.name.startswith("Test"):
                    visit(node.body, f"{prefix}::{node.name}")

        visit(mod.body, rel)
    return out


def _cap_hit(n: int, verdict: str, fields: dict[str, str]) -> bool:
    return verdict == "request changes" and (n >= 3 or (n == 2 and _prior_unfixed(fields) >= 1))


# ---------------------------------------------------------------------------------------------
# The stop gate's record
# ---------------------------------------------------------------------------------------------


GATE_HEADER = re.compile(r"^dev-team gate — (attempt (\d+)|blocked|spec-change|report) — ")


def _gate_paths(pkg: str, section: str) -> list[Path | str]:
    """What the implementer writes for the section: its code (nested sections excluded),
    `tests/unit/<section>` and its README (`interface.md` for `surface`). Not the intent tree."""
    p = _paths(pkg, section)
    return [*p["code"], p["unit"], p["readme"]]  # type: ignore[list-item]


def gate_commit(pkg: str, section: str) -> str | None:
    """Full sha of the newest commit touching the section's code, unit tree and README: the commit
    a gate record speaks for. None when no commit does. The stop gate imports it, so the record's
    writer and its reader compute the same commit."""
    return last_commit(*_gate_paths(pkg, section))


def gate_record(pkg: str, section: str) -> dict[str, object] | None:
    """The stop gate's record for the section's current commit, parsed; None when it is absent or stale.

    Keys: slot (`attempt`, `blocked`, `spec-change` or `report`), attempt (int or None),
    result (the text after `result: ` on the last non-empty line), fails (every line starting
    `FAIL`), blocked (the text after `blocked: `, or "").
    """
    f = ROOT / ".dev-team" / "gate" / pkg / f"{section}.txt"
    try:
        lines = [line.rstrip("\n") for line in f.read_text().splitlines()]
    except (OSError, UnicodeDecodeError):
        return None
    if len(lines) < 3:
        return None
    head = GATE_HEADER.match(lines[0])
    if head is None:
        return None
    value = next((line[len("commit:"):].strip() for line in lines if line.startswith("commit:")), None)
    if value is None:
        return None
    if uncommitted(*_gate_paths(pkg, section)):
        return None
    sha = gate_commit(pkg, section)
    if value == "none":
        if sha is not None:
            return None
    elif len(value) < 7 or sha is None or not sha.startswith(value):
        return None
    last = next((line for line in reversed(lines) if line.strip()), "")
    slot = "attempt" if head.group(2) else head.group(1)
    return {
        "slot": slot,
        "attempt": int(head.group(2)) if head.group(2) else None,
        "result": last[len("result: "):].strip() if last.startswith("result: ") else "",
        "fails": [line for line in lines if line.startswith("FAIL")],
        "blocked": next((line[len("blocked: "):].strip() for line in lines if line.startswith("blocked: ")), ""),
    }


def _code_after_review(pkg: str, section: str, rsha: str) -> str | None:
    """The first change to the section's code (its path, `tests/unit/<section>`,
    `tests/intent/<section>` less regeneration commits, its README) after review commit rsha;
    None when there is none. Rule 7 and `_review_covers` both read it."""
    p = _paths(pkg, section)
    return changed_since(rsha, *p["code"], p["unit"], p["intent"], p["readme"], skip_regen=(pkg, section))  # type: ignore[misc]


def _review_covers(pkg: str, section: str) -> bool:
    """True when a review round exists, its `Commit:` is readable, and the section's code is not
    newer than it: rule 7's expression."""
    n, _, rsha, _ = newest_round(pkg, section)
    if n == 0 or rsha is None:
        return False
    return _code_after_review(pkg, section, rsha) is None


def _gate_hold(pkg: str, section: str, readme: Path) -> dict[str, object] | None:
    """The gate record that may hold the row: the README exists, no review round covers the
    code, and the record is current; else None."""
    if not readme.exists() or _review_covers(pkg, section):
        return None
    return gate_record(pkg, section)


def section_state(pkg: str, section: str) -> tuple[str, str]:
    """(STATE, evidence) for one section: the first rule in the module docstring that fires."""
    p = _paths(pkg, section)
    row: dict[str, str] = p["row"]  # type: ignore[assignment]
    design: Path = p["design"]  # type: ignore[assignment]
    intent: Path = p["intent"]  # type: ignore[assignment]
    readme: Path = p["readme"]  # type: ignore[assignment]
    code: list[str] = p["code"]  # type: ignore[assignment]
    regen = (pkg, section)

    # 1. BLOCKED
    if ds := blocking_decisions(pkg, section):
        return "BLOCKED", f"{', '.join(ds)} open, no assumption"
    n, verdict, rsha, fields = newest_round(pkg, section)
    if _cap_hit(n, verdict, fields):
        k = _prior_unfixed(fields)
        return "BLOCKED", f"review r{n} request changes" + (f", {k} prior unfixed" if k else "") + " (cap)"
    record = _gate_hold(pkg, section, readme)
    if record is not None:
        result = str(record["result"])
        if record["slot"] == "blocked" and result == "blocked":
            why = str(record["blocked"]).replace(" · ", ", ") or "(no reason given)"
            return "BLOCKED", f"gate blocked: {why}"
        if record["slot"] == "attempt" and result.startswith("letting the run stop"):
            m = re.search(r"with (\d+) failure", result)
            return "BLOCKED", f"gate let through after 3 attempts, {m.group(1) if m else '?'} failures"

    spec = live_spec_changes(pkg, section)
    kinds = {e["kind"] for e in spec}

    # 2. PLAN
    if "spec-change:contract" in kinds:
        heads = [e["heading"] for e in spec if e["kind"] == "spec-change:contract"]
        return "PLAN", "open " + "; ".join(heads)

    # 3. PROBE
    for kind, token in _sources(row.get("source", "")):
        doc = DOCS / "sources" / f"{token}.md"
        if kind == "dataset" and not doc.exists():
            return "PROBE", f"dataset:{token} has no {_rel(doc)}"
        if kind == "api" and (not doc.exists() or not _has_section_heading(doc.read_text(), pkg, section)):
            return "PROBE", f"api:{token} lacks ## {pkg}/{section}"

    # 4. DESIGN
    if not design.exists():
        return "DESIGN", "no design"
    if "spec-change:design" in kinds:
        heads = [e["heading"] for e in spec if e["kind"] == "spec-change:design"]
        return "DESIGN", "open " + "; ".join(heads)
    design_rev = _rev(design)
    for c in open_changes(pkg, section):
        crev = _rev(c["path"])  # type: ignore[arg-type]
        if _newer(crev, design_rev):
            return "DESIGN", f"change {c['slug']} {_short(crev)} newer than design {_short(design_rev)}"
    for _, token in _sources(row.get("source", "")):
        doc = DOCS / "sources" / f"{token}.md"
        if doc.exists() and (prev := _probe_newer(doc, design_rev, pkg, section)):
            return "DESIGN", f"{_rel(doc)} {_short(prev)} newer than design {_short(design_rev)}"

    # 5. TEST
    if not intent.is_dir():
        return "TEST", f"no {_rel(intent)}"
    intent_rev = _rev(intent)
    if _newer(design_rev, intent_rev):
        if design_rev == UNCOMMITTED:
            return "TEST", f"uncommitted: {_rel(design)}"
        return "TEST", f"design {_short(design_rev)} newer than tests {_short(intent_rev)}"
    if "spec-change:test" in kinds:
        # every open one, so Regenerate names them all: a tester resolves only the entries it is sent
        heads = [e["heading"] for e in spec if e["kind"] == "spec-change:test"]
        return "TEST", "open " + "; ".join(heads)
    approved = [e for e in deviation_entries(pkg, section) if e["kind"] == "deviation" and _status(e) == "approved"]
    if approved:
        docs = intent_docstrings(intent)
        for e in approved:
            key = clause_key(e["Clause"])
            if key and any(clause_key(d) == key and "(deviation " not in d for d in docs.values()):
                return "TEST", f"regenerate: {e['heading']}"

    # 6. IMPLEMENT
    if not readme.exists():
        return "IMPLEMENT", f"no {_rel(readme)}"
    readme_rev = _rev(readme)
    intent_rev_nr = _rev(intent, skip_regen=regen)
    if _newer(intent_rev_nr, readme_rev):
        if intent_rev_nr == UNCOMMITTED:
            return "IMPLEMENT", f"uncommitted: {_rel(intent)}"
        return "IMPLEMENT", f"tests {_short(intent_rev_nr)} newer than README {_short(readme_rev)}"
    if record is not None and record["slot"] == "attempt" and str(record["result"]).startswith("not done (attempt "):
        return "IMPLEMENT", f"gate {record['result']}"

    # 7. REVIEW
    if n == 0:
        return "REVIEW", "no review"
    if n == 1 and (missing := _missing_letters(pkg, section)):
        return "REVIEW", f"review r1 lacks its {' and '.join(missing)} report"
    if rsha is None:
        return "REVIEW", f"review r{n} has no Commit:"
    if (after := _code_after_review(pkg, section, rsha)) is not None:
        if after == UNCOMMITTED:
            return "REVIEW", f"uncommitted: {code[0]}"
        return "REVIEW", f"code {_short(after)} newer than review r{n} {rsha[:7]}"
    if verdict == "spec-change":
        return "REVIEW", f"review r{n} spec-change, no open entry left"

    # 8. FIX n
    if verdict == "request changes":
        return f"FIX {n}", f"review r{n} request changes"

    # 9. DONE
    return "DONE", f"review r{n} approve @{rsha[:7]}"


def section_commit(pkg: str, section: str) -> str | None:
    """Short sha of the newest commit touching the section's code, unit tree, intent tree and
    README (not its design): the commit a reviewer reviews, and its report's `Commit:` (F12)."""
    p = _paths(pkg, section)
    return git("log", "-1", "--format=%h", "--", *map(_rel, (*p["code"], p["unit"], p["intent"], p["readme"]))) or None  # type: ignore[misc]


def _section_rev(pkg: str, section: str) -> str | None:
    p = _paths(pkg, section)
    return _rev(p["design"], p["intent"], p["unit"], p["readme"], *p["code"])  # type: ignore[arg-type]


def package_table(pkg: str) -> list[dict[str, object]]:
    """One dict per section: section, state, evidence, ready, round, spec, commit."""
    rows = sections(pkg)
    states = {r["section"]: section_state(pkg, r["section"]) for r in rows}
    names = set(states)
    out = []
    for r in rows:
        sec = r["section"]
        state, ev = states[sec]
        deps = [d for d in _names(r["depends on"]) if d in names and d != sec]
        ready = state not in ("DONE", "BLOCKED") and all(states[d][0] == "DONE" for d in deps)
        n = rounds(pkg, sec)
        spec = ", ".join(sorted({e["kind"] for e in live_spec_changes(pkg, sec)})) or "—"
        out.append({"section": sec, "state": state, "evidence": ev, "ready": ready,
                    "round": n, "spec": spec, "commit": _short(_section_rev(pkg, sec))})
    return out


# ---------------------------------------------------------------------------------------------
# next
# ---------------------------------------------------------------------------------------------


def _to_sync(pkg: str) -> bool:
    approved = [e for e in deviation_entries(pkg) if e["kind"] == "deviation" and _status(e) == "approved"]
    return bool(approved or open_changes(pkg))


def next_command(pkg: str, table: list[dict[str, object]] | None = None) -> str:
    """The one command to type next for pkg, every name filled in."""
    if not contract_path(pkg).exists():
        return f"/dev-team:plan-package {pkg}"
    table = package_table(pkg) if table is None else table
    for r in table:
        if r["state"] == "BLOCKED" and str(r["evidence"]).startswith("D"):
            d = str(r["evidence"]).split(",")[0].split()[0]
            return f"answer {d} in docs/decisions.md, then /dev-team:run-package {pkg}"
    for r in table:
        if r["state"] == "BLOCKED" and str(r["evidence"]).startswith("gate "):
            return (f"/dev-team:run-package {pkg} {r['section']} --step IMPLEMENT (run it again) or "
                    f"/dev-team:run-package {pkg} {r['section']} --step REVIEW (review anyway)")
    for r in table:
        if r["state"] == "BLOCKED":
            return f"/dev-team:run-package {pkg} {r['section']} --step REVIEW (one more round) or /dev-team:run-package {pkg} --defer"
    if any(r["ready"] for r in table):
        return f"/dev-team:run-package {pkg}"
    if any(r["state"] != "DONE" for r in table):
        return f"/dev-team:run-package {pkg}"
    if _to_sync(pkg):
        return f"/dev-team:sync-plan {pkg}"
    others = [name for name, _ in packages() if name != pkg]
    for other in others:
        if contract_path(other).exists() and any(r["state"] != "DONE" for r in package_table(other)):
            return f"/dev-team:run-package {other}"
    for other in others:
        if not contract_path(other).exists():
            return f"/dev-team:plan-package {other}"
    return "/dev-team:finalize-project"


def scaffold_needed(pkg: str) -> list[str]:
    """What the SCAFFOLD step must create before pkg is built in: [] when nothing."""
    root_py = ROOT / "pyproject.toml"
    if not root_py.exists():
        return ["no root pyproject.toml"]
    try:
        is_workspace = "[tool.uv.workspace]" in root_py.read_text()
    except OSError:
        return []
    pkg_py = package_root(pkg) / "pyproject.toml"
    if is_workspace and not pkg_py.exists():
        return [f"no {_rel(pkg_py)}"]
    return []


def package_report(pkg: str) -> list[str]:
    lines = [f"## {pkg}", "section · state · evidence · ready · round · open spec-change · last commit"]
    if not contract_path(pkg).exists():
        lines += [f"shipped: no (no {_rel(contract_path(pkg))})", f"next: {next_command(pkg)}"]
        return lines
    table = package_table(pkg)
    for r in table:
        lines.append(" · ".join([str(r["section"]), str(r["state"]), str(r["evidence"]),
                                 "yes" if r["ready"] else "no", str(r["round"] or "—"),
                                 str(r["spec"]), str(r["commit"])]))
    if needed := scaffold_needed(pkg):
        lines.append(f"scaffold: needed ({', '.join(needed)})")
    surface = next((r for r in table if r["section"] == "surface"), None)
    if surface is None:
        lines.append("shipped: no (no surface row)")
    else:
        lines.append("shipped: yes" if surface["state"] == "DONE" else f"shipped: no (surface {surface['state']})")
    lines.append(f"next: {next_command(pkg, table)}")
    return lines


# ---------------------------------------------------------------------------------------------
# docs/constraints.md and the Toolchain
# ---------------------------------------------------------------------------------------------


def constraints_rows(pkg: str) -> list[tuple[str, str, str, str]]:
    """(heading, dimension, command with <pkg> filled, scope) over Floor, Enforced and Measured."""
    f = DOCS / "constraints.md"
    if not f.exists():
        return []
    text = f.read_text()
    out = []
    for heading in ("Floor", "Enforced", "Measured"):
        for row in table_rows(_block(text, heading), ("command", "scope")):
            cmd = col(row, "command")
            if cmd:
                dim = col(row, "check") or col(row, "dimension")
                out.append((heading, dim, cmd.replace("<pkg>", pkg), col(row, "scope").lower() or "package"))
    return out


def guarded_items() -> list[str]:
    """The Guarded bullet texts of docs/constraints.md."""
    f = DOCS / "constraints.md"
    if not f.exists():
        return []
    return [m.group(1).strip() for m in re.finditer(r"^\s*[-*]\s+(.+)$", _block(f.read_text(), "Guarded"), re.M)]


def exceptions_rows() -> list[dict[str, str]]:
    """The Exceptions table rows of docs/constraints.md."""
    f = DOCS / "constraints.md"
    if not f.exists():
        return []
    return table_rows(_block(f.read_text(), "Exceptions"), ("path", "check"))


def toolchain_commands() -> list[str]:
    """One command per line of every fenced block under architecture.md's Toolchain heading."""
    f = DOCS / "architecture.md"
    if not f.exists():
        return []
    body = _item(f.read_text(), "Toolchain")
    out = []
    for block in re.findall(r"^\s*```[^\n]*\n(.*?)^\s*```", body, re.M | re.S):
        for line in block.splitlines():
            line = line.strip()
            if line and not line.startswith("#"):
                out.append(line)
    return out


# ---------------------------------------------------------------------------------------------
# Subagent transcripts: which section an agent run is for
# ---------------------------------------------------------------------------------------------


def _transcript_target(path: Path | str) -> tuple[str, str] | str | None:
    """(pkg, section), "scaffold", or "none" from a transcript's first `user` record; None when
    the file cannot be read."""
    try:
        with open(path, encoding="utf-8") as fh:
            for line in fh:
                try:
                    rec = json.loads(line)
                except ValueError:
                    continue
                if not isinstance(rec, dict) or rec.get("type") != "user":
                    continue
                content = (rec.get("message") or {}).get("content", "")
                if isinstance(content, list):
                    content = "\n".join(str(c.get("text", "")) for c in content if isinstance(c, dict))
                lines = str(content).splitlines()
                if any(ln.startswith("Scaffold:") for ln in lines):
                    return "scaffold"
                for ln in lines:
                    if m := re.match(r"^Section:\s+([\w.-]+)/([\w.-]+)\s*$", ln):
                        return m.group(1), m.group(2)
                return "none"
    except OSError:
        return None
    return "none"


def section_from_transcript(path: Path | str) -> tuple[str, str] | None:
    """(pkg, section) from the first `Section: <pkg>/<section>` line of a subagent transcript's
    first `user` record (the spawn prompt, verbatim — F2); None for a `Scaffold:` run, no
    `Section:` line, or an unreadable file."""
    target = _transcript_target(path)
    return target if isinstance(target, tuple) else None


def subagent_transcript(event: dict) -> Path | None:
    """The subagent transcript a hook event belongs to: `agent_transcript_path` when the event
    carries it (SubagentStop), else derived from `transcript_path` and `agent_id` (F1)."""
    if event.get("agent_transcript_path"):
        return Path(event["agent_transcript_path"])
    tp, aid = event.get("transcript_path"), event.get("agent_id")
    if tp and aid:
        return Path(tp).with_suffix("") / "subagents" / f"agent-{aid}.jsonl"
    return None


def cached_section(event: dict) -> tuple[str, str] | None:
    """section_from_transcript for a hook event, cached per agent under
    `${CLAUDE_PLUGIN_DATA}/section/<agent_id>` (else `<cwd>/.dev-team/section/<agent_id>`) as
    `<pkg>/<section>`, `scaffold` or `none`. An unreadable transcript is not cached."""
    aid = event.get("agent_id")
    base = Path(os.environ["CLAUDE_PLUGIN_DATA"]) if os.environ.get("CLAUDE_PLUGIN_DATA") else Path(event.get("cwd") or ROOT) / ".dev-team"
    cache = base / "section" / str(aid) if aid else None
    if cache is not None:
        try:
            value = cache.read_text().strip()
        except OSError:
            value = ""
        if value:
            pkg, _, sec = value.partition("/")
            return (pkg, sec) if sec else None
    path = subagent_transcript(event)
    target = _transcript_target(path) if path else None
    if target is None:
        return None
    if cache is not None:
        try:
            cache.parent.mkdir(parents=True, exist_ok=True)
            cache.write_text("/".join(target) if isinstance(target, tuple) else target)
        except OSError:
            pass
    return target if isinstance(target, tuple) else None


# ---------------------------------------------------------------------------------------------
# Flags
# ---------------------------------------------------------------------------------------------


def run_gate(pkg: str | None) -> list[str]:
    """Reasons a run may not start; empty when it may."""
    if git("rev-parse", "--is-inside-work-tree") is None:
        return ["not a git repository; git init, create a branch, and re-run"]
    fails = []
    branch = git("branch", "--show-current") or ""
    if branch in ("main", "master"):
        fails.append(f"on `{branch}`; create a feature branch and re-run")
    # -z: NUL-separated and unquoted, read unstripped. A rename or copy entry is followed by
    # its source path, skipped.
    raw = subprocess.run(["git", "status", "--porcelain", "-z", "--untracked-files=all"],
                         capture_output=True, text=True, cwd=ROOT).stdout
    entries = iter(raw.split("\0"))
    dirty = []
    for entry in entries:
        if len(entry) < 4:
            continue
        if entry[0] in "RC":
            next(entries, None)
        path = entry[3:]
        if not any(path == e or (e.endswith("/") and path.startswith(e)) for e in BASELINE_EXEMPT):
            dirty.append(path)
    if dirty:
        fails.append(f"uncommitted changes outside the user-edited files: {', '.join(dirty)}; commit or stash them and re-run")
    plugin = Path(__file__).resolve().parents[3]
    for r in unsynced_inboxes():
        fails.append(f"unsynced inbox — {r}; run python3 {plugin}/hooks/sync_decisions.py --all and commit it")
    if pkg and not contract_path(pkg).exists():
        fails.append(f"{pkg}: missing docs/packages/{pkg}/contract.md — run /dev-team:plan-package {pkg}")
    return fails


def _dunder_all(init: Path) -> set[str] | None:
    try:
        mod = ast.parse(init.read_text())
    except (OSError, SyntaxError):
        return None
    for node in mod.body:
        targets = node.targets if isinstance(node, ast.Assign) else [node.target] if isinstance(node, ast.AnnAssign) else []
        if any(isinstance(t, ast.Name) and t.id == "__all__" for t in targets) and node.value is not None:
            try:
                return set(ast.literal_eval(node.value))
            except ValueError:
                return None
    return set()


def _name_cell(row: dict[str, str]) -> str:
    """A table row's name: the first backticked span of its `name` cell (`` `Trade` (`models.py`) ``
    is `Trade`), else the cell up to its first `(`."""
    raw = next((v for h, v in row.items() if "name" in h), "")
    m = re.match(r"\s*`([^`]+)`", raw)
    return (m.group(1) if m else raw.split("(")[0]).strip("`* ").strip()


def surface_check(pkg: str) -> tuple[str, list[str]]:
    """(PASS | FAIL | n/a, reasons): __all__ vs interface.md Public names vs READMEs' Public: yes rows, and lazy import."""
    iface = DOCS / "packages" / pkg / "interface.md"
    if not iface.exists():
        return "n/a", []
    fails = []
    root = package_root(pkg)
    rows = sections(pkg)
    surface_row = next((r for r in rows if r["section"] == "surface"), None)
    top = ROOT / (surface_row["path"] if surface_row else _rel(root / "src" / pkg))
    all_names = _dunder_all(top / "__init__.py")
    if all_names is None:
        fails.append(f"no readable __all__ in {_rel(top / '__init__.py')}")
        all_names = set()
    iface_rows = table_rows(_item(iface.read_text(), "Public names"), ("name",))
    public = {_name_cell(r) for r in iface_rows if _name_cell(r)}
    # A name whose providing module lies outside every other section (a pipeline, the CLI) is the
    # surface section's own: no section README can carry its row.
    section_mods = []
    for r in rows:
        if r["section"] != "surface":
            try:
                section_mods.append(".".join((ROOT / r["path"]).resolve().relative_to(top.resolve().parent).parts))
            except ValueError:
                section_mods.append(f"{pkg}.{r['section']}")
    surface_own = {_name_cell(r) for r in iface_rows
                   if (mod := col(r, "providing")) and not any(mod == m or mod.startswith(m + ".") for m in section_mods)}
    readmes: set[str] = set()
    for r in rows:
        if r["section"] == "surface":
            continue
        f = ROOT / r["path"] / "README.md"
        if f.exists():
            for er in table_rows(_item(f.read_text(), "Entry points and interfaces"), ("name",)):
                if col(er, "public").lower().startswith("yes") and _name_cell(er):
                    readmes.add(_name_cell(er))
    for a, an, b, bn in ((all_names, "__all__", public, "interface.md Public names"),
                         (public - surface_own, "interface.md Public names", readmes, "README Public: yes rows"),
                         (readmes, "README Public: yes rows", all_names, "__all__")):
        for name in sorted(a - b):
            fails.append(f"{name}: in {an}, not in {bn}")
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1",
           "PYTHONPATH": os.pathsep.join(filter(None, [str(top.parent), os.environ.get("PYTHONPATH", "")]))}
    try:
        res = subprocess.run([sys.executable, "-X", "importtime", "-c", f"import {pkg}"],
                             capture_output=True, text=True, cwd=ROOT, env=env, timeout=120)
    except (OSError, subprocess.TimeoutExpired) as exc:
        fails.append(f"import {pkg} did not run: {exc}")
    else:
        if res.returncode != 0:
            last = (res.stderr.strip().splitlines() or ["?"])[-1]
            fails.append(f"import {pkg} failed: {last}")
        else:
            eager = sorted({m.group(1) for m in re.finditer(rf"\|\s*({re.escape(pkg)}\.[\w.]+)\s*$", res.stderr, re.M)
                            if m.group(1).split(".")[1] in {r['section'] for r in rows if r['section'] != 'surface'}})
            for mod in eager:
                fails.append(f"import {pkg} loads section module {mod} (not lazy)")
    return ("FAIL" if fails else "PASS"), fails


def repo_report() -> list[str]:
    """The repo-wide gap list, six groups, for the documenter's Known gaps."""
    pk, secs, specs, chg = [], [], [], []
    for pkg, _ in packages():
        if not contract_path(pkg).exists():
            pk.append(f"{pkg}: no contract")
            continue
        table = package_table(pkg)
        done = sum(1 for r in table if r["state"] == "DONE")
        surface = next((r for r in table if r["section"] == "surface"), None)
        if surface and surface["state"] == "DONE":
            pk.append(f"{pkg}: shipped")
        elif not any(_paths(pkg, str(r["section"]))["design"].exists() for r in table):  # type: ignore[union-attr]
            pk.append(f"{pkg}: planned")
        else:
            pk.append(f"{pkg}: building ({done}/{len(table)} DONE)")
        secs += [f"{pkg}/{r['section']}: {r['state']}" for r in table if r["state"] != "DONE"]
        specs += [e["heading"] for r in table for e in live_spec_changes(pkg, str(r["section"]))]
    for c in change_files():
        if str(c["status"]).startswith("open"):
            chg.append(str(c["slug"]))
    decs = [f"D{d['n']}: {d['question']}" for d in decisions() if d["status"].startswith(("open", "deferred"))]
    backlog: dict[str, int] = {}
    fu = DOCS / "followups.md"
    if fu.exists():
        for m in re.finditer(r"^- \[ \]\s*`?([^:`]+?)`?\s*:", fu.read_text(), re.M):
            backlog[m.group(1).strip()] = backlog.get(m.group(1).strip(), 0) + 1
    groups = [("packages", pk), ("sections", secs), ("decisions", decs), ("spec-changes", specs),
              ("changes", chg), ("backlog", [f"{t}: {n}" for t, n in backlog.items()])]
    lines = []
    for label, items in groups:
        lines.append(f"{label}:")
        lines += [f"  - {i}" for i in items] or ["  - none"]
    return lines


def upstream_packages(pkg: str) -> list[str]:
    """The `depends on` names of pkg's row in architecture.md's Packages table."""
    arch = DOCS / "architecture.md"
    if not arch.exists():
        return []
    for row in table_rows(arch.read_text(), ("package", "path")):
        if col(row, "package") == pkg:
            return _names(col(row, "depends"))
    return []


def implementer_inputs(pkg: str, section: str) -> list[str]:
    """The implementer's spawn block for one section, one `<Field>: <value>` line per field.

    The fields and how each resolves are the module docstring's `--inputs` list.
    """
    row = _row(pkg, section) or {}
    rows = {r["section"]: r for r in sections(pkg)}
    p = _paths(pkg, section)
    deps = [f"{rows[d]['path']}/README.md" for d in _names(row.get("depends on", "")) if d in rows and d != section]
    ups = []
    for dep in upstream_packages(pkg):
        iface = DOCS / "packages" / dep / "interface.md"
        ups.append(_rel(iface) if iface.exists() else f"provisional: {_rel(contract_path(dep))}")
    probes = [f"docs/sources/{token}.md" for _, token in _sources(row.get("source", ""))]
    intent: Path = p["intent"]  # type: ignore[assignment]
    n, verdict, _, _ = newest_round(pkg, section)
    review = sorted(_rel(f) for f in _reports(pkg, section).get(n, [])) if verdict in ("request changes", "spec-change") else []
    changes = [_rel(c["path"]) for c in open_changes(pkg, section)]  # type: ignore[arg-type]

    def cell(values: list[str]) -> str:
        return ", ".join(values) or "none"

    return [
        f"Section: {pkg}/{section}",
        f"Design: {_rel(p['design'])}",  # type: ignore[arg-type]
        f"Contract: {_rel(contract_path(pkg))}",
        "Repo contract: docs/architecture.md",
        f"Dependency READMEs: {cell(deps)}",
        f"Upstream interfaces: {cell(ups)}",
        f"Source probes: {cell(probes)}",
        f"Intent tests: {_rel(intent) + '/' if intent.is_dir() else 'none'}",
        f"Review: {cell(review)}",
        f"Round: {n + 1}",
        f"Change file: {cell(changes)}",
        f"Run: run-package {pkg}",
    ]


def _holds_code(pkg: str, section: str) -> bool:
    """True when the section's path holds a `.py` file, nested sections excluded; for `surface`
    the package's own `__init__.py` (the scaffold's) does not count."""
    p = _paths(pkg, section)
    code: list[str] = p["code"]  # type: ignore[assignment]
    base = ROOT / code[0]
    nested = [ROOT / c.removeprefix(":(exclude)") for c in code[1:]]
    if not base.is_dir():
        return False
    scaffold = base / "__init__.py" if section == "surface" else None
    return any(f != scaffold and not any(n == f or n in f.parents for n in nested)
               for f in base.rglob("*.py"))


def spawn_fields(pkg: str, section: str) -> list[str]:
    """The `--fields` lines for one section; the module docstring lists them."""
    p = _paths(pkg, section)
    design: Path = p["design"]  # type: ignore[assignment]
    changes = [_rel(c["path"]) for c in open_changes(pkg, section)]  # type: ignore[arg-type]
    state, evidence = section_state(pkg, section)
    if changes or (evidence.startswith("open ") and "spec-change:design" in evidence):
        mode = "delta"
    elif _holds_code(pkg, section) and not design.exists():
        mode = "document"
    else:
        mode = "new"
    design_mode = "none"
    if design.exists():
        head = design.read_text().strip().splitlines()[:5]
        if m := next((m for line in head if (m := re.match(r"\**Mode:\**\s*`?(\w+)", line.strip()))), None):
            design_mode = m.group(1)
    base = "none"
    reps = _reports(pkg, section)
    if reps:
        n = max(reps)
        files = sorted(reps[n])
        pick = (next((f for f in files if f.name.endswith("-s.md")), None)
                or (next((f for f in files if f.name.endswith("-a.md")), None) if n == 1 else None)
                or (files[0] if len(files) == 1 and not re.search(r"-r\d+-[abs]\.md$", files[0].name) else None))
        if pick and (m := re.match(r"[0-9a-f]{7,40}", _report_fields(pick).get("Commit", "").strip("`"))):
            base = git("rev-parse", "--short", m.group(0)) or m.group(0)
    return [
        f"mode: {mode}",
        f"change file: {', '.join(changes) or 'none'}",
        f"design mode: {design_mode}",
        f"diff base: {base}",
    ]


def _flag_value(argv: list[str], flag: str) -> tuple[bool, str | None]:
    """(present, value) for a flag with an optional non-flag value after it; removes both from argv."""
    if flag not in argv:
        return False, None
    i = argv.index(flag)
    argv.pop(i)
    if i < len(argv) and not argv[i].startswith("--"):
        return True, argv.pop(i)
    return True, None


def main() -> int:
    argv = sys.argv[1:]
    has_rounds, rounds_target = _flag_value(argv, "--rounds")
    has_surface, surface_pkg = _flag_value(argv, "--surface")
    has_gate, gate_pkg = _flag_value(argv, "--run-gate")
    has_inputs, inputs_target = _flag_value(argv, "--inputs")
    has_scaffold, scaffold_pkg = _flag_value(argv, "--scaffold")
    has_fields, fields_target = _flag_value(argv, "--fields")
    has_repo = "--repo" in argv
    argv = [a for a in argv if a != "--repo"]
    unknown = [a for a in argv if a.startswith("--")]
    if unknown:
        print(f"unknown flag: {' '.join(unknown)}")
        return 2
    only = argv[0] if argv else None
    code = 0
    if has_rounds:
        pkg, _, sec = (rounds_target or "").partition("/")
        if not pkg or not sec:
            print("--rounds needs a target: status.py --rounds <pkg>/<section>")
            return 2
        n = rounds(pkg, sec)
        print(f"rounds: {n}")
        print(f"next round: {n + 1}")
        print(f"commit: {section_commit(pkg, sec) or 'none'}")
    if has_gate:
        fails = run_gate(gate_pkg or only)
        print("run gate: PASS" if not fails else "run gate: FAIL")
        for f in fails:
            print(f"  - {f}")
        code |= 1 if fails else 0
    if has_surface:
        if not surface_pkg:
            print("--surface needs a package: status.py --surface <pkg>")
            return 2
        verdict, fails = surface_check(surface_pkg)
        print(f"surface: {verdict}" + (" (no interface.md)" if verdict == "n/a" else ""))
        for f in fails:
            print(f"  - {f}")
        code |= 1 if verdict == "FAIL" else 0
    if has_repo:
        if not DOCS.exists():
            print("no docs/ directory here — run from the repo root")
            return 2
        print("\n".join(repo_report()))
    if has_inputs:
        pkg, _, sec = (inputs_target or "").partition("/")
        if not pkg or not sec:
            print("--inputs needs a target: status.py --inputs <pkg>/<section>")
            return 2
        if _row(pkg, sec) is None:
            print(f"no section {sec} in {_rel(contract_path(pkg))}")
            return 2
        print("\n".join(implementer_inputs(pkg, sec)))
    if has_fields:
        pkg, _, sec = (fields_target or "").partition("/")
        if not pkg or not sec:
            print("--fields needs a target: status.py --fields <pkg>/<section>")
            return 2
        if _row(pkg, sec) is None:
            print(f"no section {sec} in {_rel(contract_path(pkg))}")
            return 2
        print("\n".join(spawn_fields(pkg, sec)))
    if has_scaffold:
        if not scaffold_pkg:
            print("--scaffold needs a package: status.py --scaffold <pkg>")
            return 2
        needed = scaffold_needed(scaffold_pkg)
        print(f"scaffold: needed ({', '.join(needed)})" if needed else "scaffold: done")
        code |= 1 if needed else 0
    if has_rounds or has_gate or has_surface or has_repo or has_inputs or has_scaffold or has_fields:
        return code
    if not DOCS.exists():
        print("no docs/ directory here — run from the repo root")
        return 2
    pkgs = packages()
    if not pkgs:
        print("no packages: docs/architecture.md has no Packages table and docs/packages/ is empty")
        print("next: /dev-team:plan-repo")
        return 0
    if only and only not in {name for name, _ in pkgs}:
        pkgs = [(only, package_root(only))]
    blocks = [package_report(pkg) for pkg, _ in pkgs if not only or pkg == only]
    print("\n\n".join("\n".join(b) for b in blocks))
    return code


if __name__ == "__main__":
    sys.exit(main())
