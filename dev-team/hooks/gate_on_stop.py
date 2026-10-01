#!/usr/bin/env python3
"""SubagentStop hook for `dev-team:implementer`: the implementer may not finish while its
section's mechanical checks are red.

Input: the hook JSON on stdin (`cwd`, `agent_id`, `agent_type`, `stop_hook_active`).

1. Scope: exit 0 unless `agent_type` is `dev-team:implementer` and `<cwd>/docs/architecture.md`
   exists.
2. Section: `agent_transcript_path` → the first `user` record's lines (status.py's
   `section_from_transcript`, the spawn prompt verbatim): `Section: <pkg>/<section>` names the
   one section this run is gated on; `Scaffold:` runs nothing (the marker
   `.dev-team/stop/scaffold` is deleted if present, the counter cleared, exit 0); an unreadable
   transcript or no `Section:` line falls back to 2.1's discovery — `HEAD~1..HEAD` when `HEAD`
   carries a `Dev-Team-Run:` trailer, plus the working tree, mapped to sections through
   status.py's `section_for_path` (a path the `surface` section would take counts only once
   `docs/packages/<pkg>/design/surface.md` exists; no section: exit 0) — with ` (from diff)`
   in the record header.
3. Marker: `<cwd>/.dev-team/stop/<pkg>/<section>` whose first line is `blocked` or
   `spec-change` (the implementer writes it before returning either) is recorded, then
   deleted with the counter; exit 0 with no check run. The record: header with `blocked` or
   `spec-change` in the attempt slot, the `commit:` line, the check lines of this run's
   earlier record when the counter exists (a gate attempt of this agent wrote it), the line
   `<reason>: <the marker's second line>` (`(no reason given)` when it has none), and
   `result: <reason>`. The fallback records each section whose marker it found, with
   ` (from diff)` after the section name. A sibling's marker is never read.
   Counter: `${CLAUDE_PLUGIN_DATA}/gate/<agent_id>` (else `<cwd>/.dev-team/gate-attempts/
   <agent_id>`) holds the attempt number; this stop adds one.
4. The run's diff: the section's paths (its code, `tests/unit/<section>`,
   `tests/intent/<section>`, its README; for `surface` also `interface.md` and
   `docs/api/<pkg>/index.md`) since the section's newest review round's `Commit:`
   (`status.newest_round`, when it is an ancestor of `HEAD`), else since the empty tree — so
   Guarded sees only what was added since the last review, and no commit ordering is assumed.
   Untracked files under those paths count as added in full.
5. Checks, every one run: the section's intent suite and its unit suite (`tests/unit/<section>`)
   first, then the Guarded grep of the diff, then `status.py --surface` for `surface`; then
   the Floor and Enforced rows of `docs/constraints.md` for the section's package — a `repo`
   row once, except a `repo` row whose command runs `pytest`, which is CI's and is written
   `SKIPPED <row>: … repo-scope pytest is CI's` (never run: it never finished inside any
   audited gate) — else the Toolchain commands; Measured rows printed, never failed on.
   An intent failure is tolerated when its `Design §<n> <item>` docstring matches the
   `Clause:` of a `proposed` or `approved` deviation entry for the section (the full item name,
   status.py's `clause_key`). The Guarded grep is pardoned by an unexpired Exceptions row.
   ELSEWHERE: a row whose every located failure (a `path:line` or `path::test` its output
   names) lies outside the section's paths is `ELSEWHERE`, not `FAIL`: the package-wide rows
   also lint and test sibling sections, often half-built under parallel implementers, and the
   implementer writes only inside its own section. A located failure whose every location lies
   under `<pkg>/tests/intent/` is `ELSEWHERE` too, whether or not the run touched it: the tester
   owns those lines (a lint, type or Guarded hit there — a Guarded hit is written `ELSEWHERE
   guarded <item> at <path>:<n> (the tester's file)`). The intent suite's own failures stay
   `FAIL` (or tolerated by a deviation), since what fails there is the code. An `xfail` cites a
   decision when a `D<n>` not followed by a digit appears on its line (`D5:`, `D5_OPEN`). The
   line stays in the record for the reviewer. The rows share what is left of a time budget below
   the hook's 600 s timeout (`DEV_TEAM_GATE_BUDGET`, default 540 s; each row at most
   `DEV_TEAM_GATE_TIMEOUT`, default 240 s). A row that runs out of time, or never starts because
   the budget is spent, is TIMEOUT, not FAIL: nothing the implementer edits makes a package-wide
   suite faster, and a hang in its own code still fails its own suites.
6. Every line goes to `<cwd>/.dev-team/gate/<pkg>/<section>.txt`, header `dev-team gate —
   attempt n — <stamp> — section <pkg>/<section>`, the stamp the time the record is written,
   then the `commit:` line, the check lines and the `result:` line. The fallback writes the
   same record for each section it found, each with its own `commit:` line.
7. No FAIL: delete the counter, exit 0. A FAIL before attempt 3: the FAIL lines to stderr,
   exit 2, the text naming the 2.2 retry rule (§Project convention rule 4: amend when
   `git log -1 --format=%s` starts with the section's scope, else a second commit with the same
   summary and trailer; from attempt 2 naming `debugging-and-error-recovery`), and saying that
   every finish is a hand-back whose first line is `Result:` — a FAIL in a file the implementer
   may not edit is `Result: blocked` with the gate lines. Attempt 3: the FAIL lines to stderr,
   delete the counter, exit 0.
8. Malformed stdin or any exception: report it on stderr and exit 0 (fail open, reported).

By hand, `python3 gate_on_stop.py --report [--base <rev>]` from the repo root runs the same
checks of step 5 over the diff from `<rev>` (default `HEAD`) to the working tree, with no
counter and no marker, and writes the same per-section files with `report` where the attempt
goes.
It prints the file and exits 1 on a FAIL line, 2 on a bad argument. The pair skill runs it at
wrap-up, so the reviewer of hand-made code reads a gate record of that code, not of the last
implementer's.

The record's lines, in order (status.py and the reviewer read them by these names):

1. **header** — `dev-team gate — <slot> — <stamp> — section <pkg>/<section>`.
2. **commit** — `commit: <short sha>`, the newest commit touching the section's code, unit
   tree and README (status.py's `gate_commit`), or `commit: none`.
3. **checks** — one line per check; its first word is PASS, FAIL, ELSEWHERE, TOLERATED,
   TIMEOUT, SKIPPED or MEASURED.
4. **marker** — `blocked: <the marker's second line>` or `spec-change: <the entry heading>`,
   on a marker stop only.
5. **result** — the last line, `result: <value>`.

The header's slot:

1. **attempt** — `attempt <n>`, a stop that ran the checks.
2. **blocked** — the implementer's marker said `blocked`.
3. **spec-change** — the marker said `spec-change`.
4. **report** — `--report`, run by hand.

The `result:` values:

1. **pass** — no FAIL line; a note follows for ELSEWHERE, TIMEOUT and SKIPPED lines.
2. **not done** — `not done (attempt <n> of 3)`: a FAIL before the third attempt.
3. **letting the run stop** — `letting the run stop after 3 attempts with <k> failures`.
4. **blocked** — a `blocked` marker stop.
5. **spec-change** — a `spec-change` marker stop.
6. **fail** — `fail (<k> failures, report since <rev>)`, `--report` only.

The parsers are status.py's, imported; there is no copy of any of them here.
"""

from __future__ import annotations

import datetime as dt
import json
import os
import re
import subprocess
import sys
from fnmatch import fnmatch
from pathlib import Path

PLUGIN_ROOT = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parents[1])
STATUS_PY = PLUGIN_ROOT / "skills" / "status" / "scripts" / "status.py"
sys.path.insert(0, str(STATUS_PY.parent))
sys.dont_write_bytecode = True  # no __pycache__ inside the installed plugin
import status  # noqa: E402

AGENT = "dev-team:implementer"
MARKER_REASONS = ("blocked", "spec-change")
MAX_ATTEMPTS = 3
EMPTY_TREE = "4b825dc642cb6eb9a060e54bf8d69288fbee4904"
TIMEOUT = int(os.environ.get("DEV_TEAM_GATE_TIMEOUT") or 240)
BUDGET = int(os.environ.get("DEV_TEAM_GATE_BUDGET") or 540)  # below hooks.json's 600 s

# Guarded items on added lines: (the name a FAIL line prints, pattern). .py files only, so a
# README that quotes one is not a hit.
ADDED = (
    ("# noqa", re.compile(r"#\s*noqa\b", re.I)),
    ("# type: ignore", re.compile(r"#\s*type:\s*ignore\b")),
    ("# pragma: no cover", re.compile(r"#\s*pragma:\s*no\s*cover\b")),
    ("@pytest.mark.skip", re.compile(r"@pytest\.mark\.skip")),
)
XFAIL = re.compile(r"xfail")
DECISION = re.compile(r"\bD\d+(?!\d)")

# The word an Exceptions row's `check` cell must contain to pardon each item, by name prefix.
EXCEPTION_WORD = {
    "# noqa": "noqa", "# type: ignore": "type: ignore", "# pragma: no cover": "no cover",
    "@pytest.mark.skip": "skip", "xfail": "xfail", "removed assert": "assert",
    "removed pytest.raises": "raises", "lowered threshold": "threshold",
}


def _run(cmd: list[str] | str, cwd: Path, timeout: int = TIMEOUT) -> tuple[int, str]:
    """(exit code, stdout + stderr) of a command; 124 on a timeout, 127 when it cannot start."""
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        res = subprocess.run(cmd, cwd=cwd, capture_output=True, text=True, timeout=timeout,
                             shell=isinstance(cmd, str), env=env)
    except subprocess.TimeoutExpired:
        return 124, f"timed out after {timeout}s"
    except OSError as exc:
        return 127, str(exc)
    return res.returncode, (res.stdout or "") + (res.stderr or "")


def _tail(text: str, n: int = 3) -> str:
    """A failure's detail on one line: every `path:line` it names (up to ten), then its last n lines."""
    lines = [line.strip() for line in text.strip().splitlines() if line.strip()]
    located = [ln for ln in lines if re.match(r"[\w./-]+\.\w+:\d+", ln)][:10]
    rest = [ln for ln in lines[-n:] if ln not in located]
    return " | ".join(located + rest) if lines else "no output"


# ---------------------------------------------------------------------------------------------
# The run's diff
# ---------------------------------------------------------------------------------------------


def _base() -> str | None:
    """The commit (or empty tree) the run's diff starts from; None outside a git repo."""
    if status.git("rev-parse", "--is-inside-work-tree") is None:
        return None
    if status.git("rev-parse", "--verify", "-q", "HEAD") is None:
        return EMPTY_TREE
    body = status.git("log", "-1", "--format=%B", "HEAD") or ""
    if not re.search(r"^Dev-Team-Run:", body, re.M):
        return "HEAD"
    return "HEAD~1" if status.git("rev-parse", "--verify", "-q", "HEAD~1") else EMPTY_TREE


def _untracked(paths: list[str] | None = None) -> list[str]:
    """Untracked, unignored files; under paths (git pathspecs) when given."""
    spec = ["--", *paths] if paths else []
    raw = status.git("ls-files", "--others", "--exclude-standard", "-z", *spec) or ""
    return [p for p in raw.split("\0") if p]


def diff_paths(base: str, paths: list[str] | None = None) -> list[str]:
    """Every path changed since base, staged or not, and untracked; under paths when given."""
    spec = ["--", *paths] if paths else []
    changed = (status.git("diff", "--name-only", "-z", base, *spec) or "").split("\0")
    return sorted({p for p in changed + _untracked(paths) if p})


def diff_lines(base: str, paths: list[str] | None = None) -> list[tuple[str, str, int, str]]:
    """(path, '+' or '-', line number, text) for every added and removed line since base, under
    paths when given.

    Added lines carry their new line number, removed lines their old one. An untracked file
    counts as added in full.
    """
    out: list[tuple[str, str, int, str]] = []
    spec = ["--", *paths] if paths else []
    raw = status.git("diff", "-U0", "--no-color", "--no-ext-diff", base, *spec) or ""
    path, old, new = "", 0, 0
    for line in raw.splitlines():
        if line.startswith("+++ "):
            path = line[6:] if line.startswith("+++ b/") else ""
        elif line.startswith("--- "):
            continue
        elif line.startswith("@@"):
            m = re.match(r"@@ -(\d+)(?:,\d+)? \+(\d+)(?:,\d+)? @@", line)
            old, new = (int(m.group(1)), int(m.group(2))) if m else (0, 0)
        elif path and line.startswith("+"):
            out.append((path, "+", new, line[1:]))
            new += 1
        elif path and line.startswith("-"):
            out.append((path, "-", old, line[1:]))
            old += 1
    for rel in _untracked(paths):
        try:
            text = (status.ROOT / rel).read_text()
        except (OSError, UnicodeDecodeError):
            continue
        out += [(rel, "+", i, t) for i, t in enumerate(text.splitlines(), 1)]
    return out


def section_paths(pkg: str, section: str) -> list[str]:
    """The section's paths as git pathspecs: its code (nested sections excluded), unit and intent
    trees and README; for `surface` also `interface.md` and `docs/api/<pkg>/index.md` (and the
    pre-2.2 `docs/api/<pkg>.md`)."""
    p = status._paths(pkg, section)
    out = [*map(status._rel, p["code"]), status._rel(p["unit"]), status._rel(p["intent"]), status._rel(p["readme"])]  # type: ignore[arg-type]
    if section == "surface":
        out += [status._rel(status.DOCS / "packages" / pkg / "interface.md"), status._rel(status.DOCS / "api" / pkg / "index.md"),
                status._rel(status.DOCS / "api" / f"{pkg}.md")]
    return list(dict.fromkeys(out))


def _in_section(path: str, pkg: str, section: str) -> bool:
    """True when a repo-relative path lies under the section's paths."""
    if status.section_for_path(status.ROOT / path) == (pkg, section):
        return True
    return path in {s for s in section_paths(pkg, section) if not s.startswith(":(")}


def _own_head(pkg: str, section: str) -> bool:
    """True when `HEAD`'s summary starts with the section's scope: the run's own commit."""
    return (status.git("log", "-1", "--format=%s") or "").startswith(f"{pkg}/{section}:")


def touched_paths(pkg: str, section: str, diff: list[str]) -> set[str]:
    """What the run touched: the section diff's paths, the tracked files changed in the working
    tree (staged or not), and `HEAD`'s files when `HEAD` is the run's own commit. The Guarded
    threshold check reads it for `docs/constraints.md`."""
    out = set(diff)
    if status.git("rev-parse", "--verify", "-q", "HEAD") is not None:
        out |= {p for p in (status.git("diff", "--name-only", "-z", "HEAD") or "").split("\0") if p}
        if _own_head(pkg, section):
            files = status.git("show", "--name-only", "-z", "--format=", "HEAD") or ""
            out |= {p for p in files.split("\0") if p.strip()}
    return {p.strip() for p in out}


def review_base(pkg: str, section: str) -> str:
    """The newest review round's `Commit:` when it is an ancestor of `HEAD`, else the empty tree."""
    sha = status.newest_round(pkg, section)[2]
    if sha and status.git("merge-base", "--is-ancestor", sha, "HEAD") is not None:
        return sha
    return EMPTY_TREE


def gated_sections(paths: list[str]) -> list[tuple[str, str]]:
    """(pkg, section) for every section a path belongs to; surface only once its design exists."""
    found: set[tuple[str, str]] = set()
    for p in paths:
        hit = status.section_for_path(status.ROOT / p)
        if hit is None:
            continue
        pkg, section = hit
        if section == "surface" and not (status.DOCS / "packages" / pkg / "design" / "surface.md").exists():
            continue
        found.add(hit)
    return sorted(found)


# ---------------------------------------------------------------------------------------------
# Checks
# ---------------------------------------------------------------------------------------------


LOCATED = re.compile(r"([\w./-]+\.pyi?)(?=:\d|::|\s+-\s)|(?:ERROR collecting|Would reformat:) ([\w./-]+\.pyi?)")


def _located(out: str) -> set[str]:
    """Repo-relative paths of the files a check's output names at a line or test, in the repo."""
    roots = [status.ROOT, *(path for _, path in status.packages())]
    found: set[str] = set()
    for m in LOCATED.finditer(out):
        raw = (m.group(1) or m.group(2)).removeprefix("./")
        for base in roots:
            path = base / raw
            if path.is_file():
                try:
                    found.add(path.resolve().relative_to(status.ROOT.resolve()).as_posix())
                except ValueError:
                    pass
                break
    return found


def _elsewhere(out: str, touched: set[str], section: tuple[str, str] | None = None) -> list[str]:
    """Where a failure lies when it is not the run's to fix; else [] (it is, or cannot be placed).

    With a section: the sorted located files, when none is the run's to edit — outside the
    section's paths, or an intent test (the tester's file), touched or not. Without one (the
    2.1 discovery and `--report`): the intent-test directories, when every located file is an
    intent test the run did not touch.
    """
    located = _located(out)
    if not located:
        return []
    if section is not None:
        return [] if any(_in_section(p, *section) and not _is_intent(p) for p in located) else sorted(located)
    if any("/tests/intent/" not in f"/{p}" or p in touched for p in located):
        return []
    return sorted({re.sub(r"(^|.*/)(tests/intent/[^/]+)/.*$", r"\1\2/", p) for p in located})


def _is_intent(path: str) -> bool:
    """True for a repo-relative path under a package's `tests/intent/`."""
    return "/tests/intent/" in f"/{path}"


def _row(label: str, cmd: str, code: int, out: str, touched: set[str], timeout: int = TIMEOUT,
         section: tuple[str, str] | None = None) -> str:
    if code == 0:
        return f"PASS {label}: {cmd}"
    if code == 124 and out.startswith("timed out"):
        return f"TIMEOUT {label}: {cmd} did not finish in {timeout}s"
    where = _elsewhere(out, touched, section)
    if where and section is not None:
        return (f"ELSEWHERE {label}: {cmd} exited {code}, every failure outside {'/'.join(section)} "
                f"or in intent tests ({', '.join(where)}): {_tail(out)}")
    if where:
        return (f"ELSEWHERE {label}: {cmd} exited {code}, every failure in intent tests this run may not "
                f"edit ({', '.join(where)}): {_tail(out)}")
    return f"FAIL {label}: {cmd} exited {code}: {_tail(out)}"


def _timed(cmd: str, deadline: float) -> tuple[int, str, int]:
    """(code, output, the timeout it ran under); (125, "", 0) when the budget is spent."""
    import time

    left = int(deadline - time.monotonic())
    if left < 5:
        return 125, "", 0
    limit = min(TIMEOUT, left)
    code, out = _run(cmd, status.ROOT, limit)
    return code, out, limit


def _unrun(label: str, cmd: str) -> str:
    return f"TIMEOUT {label}: {cmd} not run: the gate's {BUDGET}s budget was spent"


def check_rows(pkgs: list[str], touched: set[str] | None = None, deadline: float | None = None,
               section: tuple[str, str] | None = None) -> list[str]:
    """Floor and Enforced rows as PASS/FAIL/ELSEWHERE/TIMEOUT, Measured rows as MEASURED; else the
    Toolchain. Every row shares what is left of the budget until deadline. A `repo` row whose
    command runs pytest is SKIPPED when gating a section: CI's, never run here."""
    import time

    touched = touched or set()
    deadline = deadline if deadline is not None else time.monotonic() + BUDGET
    lines: list[str] = []
    seen: set[str] = set()
    if (status.DOCS / "constraints.md").exists():
        for pkg in pkgs:
            for heading, dim, cmd, scope in status.constraints_rows(pkg):
                key = f"repo {heading} {dim}" if scope.startswith("repo") else cmd
                if key in seen:
                    continue
                seen.add(key)
                what = dim or cmd
                if section is not None and scope.startswith("repo") and "pytest" in cmd:
                    lines.append(f"SKIPPED {what}: {cmd} not run: repo-scope pytest is CI's")
                    continue
                code, out, limit = _timed(cmd, deadline)
                if code == 125:
                    lines.append(_unrun(f"{what} ({pkg})", cmd))
                elif heading == "Measured":
                    last = [ln for ln in out.strip().splitlines() if ln.strip()]
                    lines.append(f"MEASURED {what}: {last[-1].strip() if last else 'no output'}")
                else:
                    lines.append(_row(f"{what} ({pkg})", cmd, code, out, touched, limit, section))
        return lines
    for pkg in pkgs:
        for cmd in status.toolchain_commands():
            cmd = cmd.replace("<pkg>", pkg)
            if cmd in seen:
                continue
            seen.add(cmd)
            code, out, limit = _timed(cmd, deadline)
            lines.append(_unrun("toolchain", cmd) if code == 125
                         else _row("toolchain", cmd, code, out, touched, limit, section))
    return lines


def _cited(doc: str) -> str:
    """The text between `Design ` and the first `:` of a docstring, whitespace-normalized."""
    m = re.search(r"Design\s+([^:]*)", doc, re.I)
    return " ".join(m.group(1).split()).lower() if m else ""


def _tolerating(doc: str, entries: list[dict[str, str]]) -> dict[str, str] | None:
    """The proposed or approved deviation entry whose Clause the docstring cites, if any."""
    cited, key = _cited(doc), status.clause_key(doc)
    if not cited:
        return None
    for e in entries:
        clause = " ".join(e.get("Clause", "").strip("`*_ ").split()).lower()
        if clause and (cited in clause or clause in cited or (key and status.clause_key(clause) == key)):
            return e
    return None


def _entry_status(e: dict[str, str]) -> str:
    value = e.get("Status", "").strip("`*_ ").lower().split()
    return value[0] if value else ""


def check_intent(pkg: str, section: str) -> list[str]:
    """The section's intent suite, one line per node id; failures cited by a deviation tolerated."""
    root = status.package_root(pkg)
    tree = root / "tests" / "intent" / section
    if not tree.is_dir():
        return [f"FAIL intent {pkg}/{section}: no {status._rel(tree)}/ to run"]
    runner = ["uv", "run"] if (status.ROOT / "uv.lock").exists() else ["python3", "-m"]
    rel_tree = tree.relative_to(root).as_posix()
    code, out = _run([*runner, "pytest", rel_tree, "-q", "-p", "no:cacheprovider", "--tb=line", "-rfEpxX"], root, 300)
    prefix = status._rel(root)
    prefix = "" if prefix == "." else prefix + "/"
    docs = status.intent_docstrings(tree)
    entries = [e for e in status.deviation_entries(pkg, section)
               if e["kind"] == "deviation" and _entry_status(e) in ("proposed", "approved")]
    lines: list[str] = []
    for m in re.finditer(r"^(PASSED|FAILED|ERROR|XFAIL|XPASS)\s+(\S+?::\S+)", out, re.M):
        outcome, node = m.group(1), m.group(2)
        if outcome in ("PASSED", "XFAIL", "XPASS"):
            lines.append(f"PASS intent {node}" + ("" if outcome == "PASSED" else f" ({outcome.lower()})"))
            continue
        bare = re.sub(r"\[.*\]$", "", node)
        doc = docs.get(prefix + bare, docs.get(bare, ""))
        entry = _tolerating(doc, entries) if outcome == "FAILED" else None
        if entry:
            lines.append(f"TOLERATED intent {node} ({entry['heading']})")
        else:
            lines.append(f"FAIL intent {node}" + (" (error)" if outcome == "ERROR" else ""))
    if code not in (0, 1) and not any(ln.startswith("FAIL") for ln in lines):
        lines.append(f"FAIL intent {pkg}/{section}: pytest exited {code}: {_tail(out)}")
    elif code == 1 and not any(ln.startswith(("FAIL", "TOLERATED")) for ln in lines):
        lines.append(f"FAIL intent {pkg}/{section}: pytest exited 1: {_tail(out)}")
    return lines


def check_unit(pkg: str, section: str) -> list[str]:
    """The section's unit suite (`tests/unit/<section>`), one line."""
    root = status.package_root(pkg)
    tree = root / "tests" / "unit" / section
    if not tree.is_dir():
        return [f"FAIL unit {pkg}/{section}: no {status._rel(tree)}/ to run"]
    runner = ["uv", "run"] if (status.ROOT / "uv.lock").exists() else ["python3", "-m"]
    code, out = _run([*runner, "pytest", tree.relative_to(root).as_posix(), "-q", "-p", "no:cacheprovider", "--tb=line"], root, 300)
    if code == 0:
        m = re.search(r"(\d+) passed", out)
        return [f"PASS unit {pkg}/{section}: {m.group(1) if m else 0} passed"]
    return [f"FAIL unit {pkg}/{section}: pytest exited {code}: {_tail(out)}"]


def _glob(pattern: str, path: str) -> bool:
    """fnmatch, `*` crossing `/`; a bare directory also covers everything under it."""
    return fnmatch(path, pattern) or path.startswith(pattern.rstrip("/") + "/")


def _pardoned(item: str, path: str, exceptions: list[dict[str, str]], today: dt.date) -> bool:
    """An Exceptions row whose glob matches path, whose check names item, and has not expired."""
    word = next(w for name, w in EXCEPTION_WORD.items() if item.startswith(name))
    for row in exceptions:
        glob = status.col(row, "path")
        if not glob or not _glob(glob, path) or word not in status.col(row, "check").lower():
            continue
        m = re.search(r"\d{4}-\d{2}-\d{2}", status.col(row, "expir"))
        if m is None or dt.date.fromisoformat(m.group(0)) >= today:
            return True
    return False


def _is_test(path: str) -> bool:
    name = path.rsplit("/", 1)[-1]
    return path.endswith(".py") and ("/tests/" in f"/{path}" or name.startswith("test_") or name.endswith("_test.py"))


def _thresholds(text: str) -> dict[str, list[float]]:
    """Floor and Enforced rows of a constraints.md text: first cell → the numbers in its threshold cell."""
    out: dict[str, list[float]] = {}
    for heading in ("Floor", "Enforced"):
        for row in status.table_rows(status._block(text, heading), ("threshold",)):
            name = next(iter(row.values()), "").strip("`* ")
            out[f"{heading}/{name}"] = [float(n) for n in re.findall(r"\d+(?:\.\d+)?", status.col(row, "threshold"))]
    return out


def check_guarded(base: str, paths: list[str], pathspec: list[str] | None = None, before: str | None = None,
                  intent_elsewhere: bool = False) -> list[str]:
    """Guarded items on the lines added or removed since base (under pathspec when given); a
    lowered threshold when `docs/constraints.md` is in paths, compared with its text at before
    (default base). With intent_elsewhere (a section run), a hit in an intent test is the
    tester's line: ELSEWHERE, not FAIL."""
    exceptions = status.exceptions_rows()
    today = dt.date.today()
    lines = diff_lines(base, pathspec)
    hits: list[tuple[str, str, int]] = []
    added_by_file: dict[str, set[str]] = {}
    for path, sign, _, text in lines:
        if sign == "+":
            added_by_file.setdefault(path, set()).add(text.strip())
    for path, sign, n, text in lines:
        if not path.endswith(".py"):
            continue
        if sign == "+":
            hits += [(name, path, n) for name, rx in ADDED if rx.search(text)]
            if XFAIL.search(text) and not DECISION.search(text):
                hits.append(("xfail without a D<n>", path, n))
        elif _is_test(path) and (status.ROOT / path).exists() and text.strip() not in added_by_file.get(path, set()):
            if text.strip().startswith("assert "):
                hits.append(("removed assert", path, n))
            elif "pytest.raises" in text:
                hits.append(("removed pytest.raises", path, n))
    if "docs/constraints.md" in paths:
        rev = before or base
        prior = status.git("show", f"{rev}:docs/constraints.md") if rev != EMPTY_TREE else None
        after_file = status.DOCS / "constraints.md"
        if prior and after_file.exists():
            old, new = _thresholds(prior), _thresholds(after_file.read_text())
            for name, nums in old.items():
                if name in new and any(b < a for a, b in zip(nums, new[name])):
                    hits.append((f"lowered threshold {name}", "docs/constraints.md", 0))
    out = []
    for item, path, n in hits:
        if _pardoned(item, path, exceptions, today):
            out.append(f"PASS guarded {item} at {path}:{n} (Exceptions row)")
        elif intent_elsewhere and _is_intent(path):
            out.append(f"ELSEWHERE guarded {item} at {path}:{n} (the tester's file)")
        else:
            out.append(f"FAIL guarded {item} at {path}:{n}")
    if not hits:
        out.append("PASS guarded: nothing in the diff")
    return out


def check_surface(pkg: str) -> list[str]:
    code, out = _run([sys.executable, str(STATUS_PY), "--surface", pkg], status.ROOT, 180)
    return [f"PASS surface {pkg}"] if code == 0 else [f"FAIL surface: {' | '.join(ln.strip() for ln in out.strip().splitlines())}"]


# ---------------------------------------------------------------------------------------------
# The gate
# ---------------------------------------------------------------------------------------------


def _counter(cwd: Path, agent_id: str) -> Path:
    safe = re.sub(r"[^\w.-]", "_", agent_id or "unknown")
    data = os.environ.get("CLAUDE_PLUGIN_DATA")
    return (Path(data) / "gate" / safe) if data else (cwd / ".dev-team" / "gate-attempts" / safe)


def _clear(counter: Path) -> None:
    try:
        counter.unlink()
    except FileNotFoundError:
        pass


def run_checks(base: str, section: tuple[str, str]) -> tuple[list[tuple[str, str]], list[str]]:
    """([section], one line per check) for the one section this run is gated on, over its paths
    since base."""
    import time

    start = time.monotonic()
    pkg, sec = section
    spec = section_paths(pkg, sec)
    diff = diff_paths(base, spec)
    touched = touched_paths(pkg, sec, diff)
    # The section's own checks first: they are what the implementer can fix, and they must run.
    own = check_intent(pkg, sec) + check_unit(pkg, sec)
    before = base if base != EMPTY_TREE else ("HEAD~1" if _own_head(pkg, sec) and status.git(
        "rev-parse", "--verify", "-q", "HEAD~1") else "HEAD")
    own += check_guarded(base, sorted(touched), spec, before, intent_elsewhere=True)
    if sec == "surface":
        own += check_surface(pkg)
    lines = check_rows([pkg], touched, start + BUDGET, section)
    return [section], lines + own


def run_checks_legacy(base: str | None) -> tuple[list[tuple[str, str]], list[str]]:
    """2.1's discovery: (sections in the diff since base, one line per check); no sections, no
    checks. The fallback when the transcript names no section, and `--report`."""
    paths = diff_paths(base) if base else []
    targets = gated_sections(paths)
    if not targets or base is None:
        return targets, []
    import time

    start = time.monotonic()
    pkgs = sorted({pkg for pkg, _ in targets})
    # The section's own checks first: they are what the implementer can fix, and they must run.
    own: list[str] = []
    for pkg, section in targets:
        own += check_intent(pkg, section)
    own += check_guarded(base, paths)
    for pkg in sorted({pkg for pkg, section in targets if section == "surface"}):
        own += check_surface(pkg)
    lines = check_rows(pkgs, set(paths), start + BUDGET)
    return targets, lines + own


def _record_path(cwd: Path, pkg: str, section: str) -> Path:
    return cwd / ".dev-team" / "gate" / pkg / f"{section}.txt"


def write_records(cwd: Path, targets: list[tuple[str, str]], header: str, lines: list[str],
                  outcome: str) -> list[Path]:
    """The record, once per section in the run: `.dev-team/gate/<pkg>/<section>.txt` — header,
    `commit: <short sha>` (status.py's `gate_commit` for that section, or `none`), lines, outcome."""
    out = []
    for pkg, section in targets:
        sha = status.gate_commit(pkg, section)
        path = _record_path(cwd, pkg, section)
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text("\n".join([header, f"commit: {sha[:7] if sha else 'none'}", *lines, outcome]) + "\n")
        out.append(path)
    return out


def _outcome_note(lines: list[str]) -> str:
    notes = []
    for word, what in (("ELSEWHERE", "failing elsewhere"), ("TIMEOUT", "out of time"), ("SKIPPED", "skipped")):
        n = sum(1 for ln in lines if ln.startswith(word))
        if n:
            notes.append(f"{n} check{'s' * (n != 1)} {what}")
    return f" ({'; '.join(notes)})" if notes else ""


def report(cwd: Path, base: str) -> int:
    """`--report [--base <rev>]`: the same checks over base..working tree, run by hand.

    No counter and no marker: nothing is stopped. Writes the per-section records exactly as a
    stop does, with `report` in the header's attempt slot, prints it, and exits 1 on a FAIL line.
    """
    if not (cwd / "docs" / "architecture.md").exists():
        print("dev-team gate: no docs/architecture.md here — run from the repo root", file=sys.stderr)
        return 2
    status.set_root(cwd)
    if status.git("rev-parse", "--verify", "-q", f"{base}^{{commit}}") is None:
        print(f"dev-team gate: --base {base} is not a commit", file=sys.stderr)
        return 2
    targets, lines = run_checks_legacy(base)
    if not targets:
        print(f"dev-team gate: no section in the diff since {base}", file=sys.stderr)
        return 0
    fails = [ln for ln in lines if ln.startswith("FAIL")]
    names = ", ".join(f"{p}/{s}" for p, s in targets)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outcome = ("result: pass" + _outcome_note(lines) if not fails
               else f"result: fail ({len(fails)} failure{'s' * (len(fails) != 1)}, report since {base})")
    records = write_records(cwd, targets, f"dev-team gate — report — {stamp} — sections {names}", lines, outcome)
    print("".join(r.read_text() for r in records), end="")
    return 1 if fails else 0


def _stop_reason(marker: Path) -> bool:
    """True when the marker file's first line is `blocked` or `spec-change`."""
    if not marker.is_file():
        return False
    first = (marker.read_text().strip().splitlines() or [""])[0].strip().lower()
    return first in MARKER_REASONS


CHECK_WORDS = ("PASS", "FAIL", "ELSEWHERE", "TOLERATED", "TIMEOUT", "SKIPPED", "MEASURED")


def record_marker(cwd: Path, marker: Path, section: tuple[str, str], counter: Path, suffix: str = "") -> Path:
    """The record of a marker stop: a header with the marker's reason in the attempt slot, the
    `commit:` line, the check lines of this run's earlier record (kept only when the attempt
    counter exists, i.e. this agent already ran a gate attempt), `<reason>: <detail>`, and
    `result: <reason>`."""
    text = marker.read_text().strip().splitlines()
    reason = text[0].strip().lower()
    detail = (text[1].strip() if len(text) > 1 else "") or "(no reason given)"
    carried: list[str] = []
    old = _record_path(cwd, *section)
    if counter.is_file() and old.is_file():
        carried = [ln for ln in old.read_text().splitlines() if ln.split(" ", 1)[0] in CHECK_WORDS]
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    header = f"dev-team gate — {reason} — {stamp} — section {'/'.join(section)}{suffix}"
    return write_records(cwd, [section], header, [*carried, f"{reason}: {detail}"], f"result: {reason}")[0]


def _retry_message(n: int, targets: list[tuple[str, str]], fails: list[str]) -> str:
    scope = ", ".join(f"`{p}/{s}:`" for p, s in targets)
    msg = [f"dev-team gate: not done — fix these, stage the fix, then commit per §Project convention rule 4: "
           f"when `git log -1 --format=%s` starts with {scope} run `git commit --amend --no-edit -- <paths>`, "
           f"otherwise make a second commit with the same summary and trailer — and finish again "
           f"(attempt {n} of {MAX_ATTEMPTS}):", *fails]
    if n == 2:
        msg.append("Two attempts: invoke `debugging-and-error-recovery` with the Skill tool before the third.")
    msg.append("Every finish is a hand-back whose first line is `Result:`. A FAIL in a file you may not edit "
               "is not yours to fix: write your marker and hand back `Result: blocked` with these lines.")
    msg.append("When you finish, hand back an amendment, not the full report again: `Result:`, `Amends:`, "
               "`Gate:`, `Fixed:` and the amended `Commit:` (implementer.md, Return message), as your final "
               "text: your hand-back tool delivers one report and your first report used it. The caller "
               "already holds that report and takes your last turn as your answer."
               + (" This is your last retry: the next finish ends the run whatever the checks find, so "
                  "if anything is still red, write `Gate: let through after 3 attempts`." if n == 2 else ""))
    return "\n".join(msg)


def gate(event: dict) -> int:
    cwd = Path(event["cwd"]).resolve()
    if event.get("agent_type") != AGENT or not (cwd / "docs" / "architecture.md").exists():
        return 0
    counter = _counter(cwd, str(event.get("agent_id") or ""))
    status.set_root(cwd)
    transcript = status.subagent_transcript(event)
    target = status._transcript_target(transcript) if transcript else None
    stop = cwd / ".dev-team" / "stop"
    if target == "scaffold":
        if (stop / "scaffold").is_file():
            (stop / "scaffold").unlink()
        _clear(counter)
        print("dev-team gate: scaffold run — no section in this run's diff", file=sys.stderr)
        return 0
    section = status.section_from_transcript(transcript) if isinstance(target, tuple) else None

    base: str | None = None
    if section is not None:
        markers = [(section, stop / section[0] / section[1], "")]
    else:
        base = _base()
        paths = diff_paths(base) if base else []
        markers = [((pkg, sec), stop / pkg / sec, " (from diff)") for pkg, sec in gated_sections(paths)]
    stopped = False
    for target_section, marker, suffix in markers:
        if _stop_reason(marker):
            record_marker(cwd, marker, target_section, counter, suffix)
            marker.unlink()
            stopped = True
    if stopped:
        _clear(counter)
        return 0
    try:
        n = int(counter.read_text().strip()) + 1
    except (OSError, ValueError):
        n = 1
    counter.parent.mkdir(parents=True, exist_ok=True)
    counter.write_text(f"{n}\n")

    if section is not None:
        targets, lines = run_checks(review_base(*section), section)
        names = f"section {'/'.join(section)}"
    else:
        targets, lines = run_checks_legacy(base)
        names = f"section{'s' * (len(targets) != 1)} {', '.join(f'{p}/{s}' for p, s in targets)} (from diff)"
    if not targets:
        _clear(counter)
        print("dev-team gate: no section in this run's diff", file=sys.stderr)
        return 0
    fails = [ln for ln in lines if ln.startswith("FAIL")]

    if not fails:
        outcome = "result: pass" + _outcome_note(lines)
    elif n < MAX_ATTEMPTS:
        outcome = f"result: not done (attempt {n} of {MAX_ATTEMPTS})"
    else:
        outcome = f"result: letting the run stop after {MAX_ATTEMPTS} attempts with {len(fails)} failure{'s' * (len(fails) != 1)}"
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    records = write_records(cwd, targets, f"dev-team gate — attempt {n} — {stamp} — {names}", lines, outcome)
    where = ", ".join(p.relative_to(cwd).as_posix() for p in records)

    if not fails:
        _clear(counter)
        return 0
    if n < MAX_ATTEMPTS:
        print(_retry_message(n, targets, fails), file=sys.stderr)
        return 2
    print("\n".join([f"dev-team gate: letting the run stop after {MAX_ATTEMPTS} attempts with these failures — "
                     f"the reviewer will see them in {where}:", *fails]), file=sys.stderr)
    _clear(counter)
    return 0


def main() -> int:
    argv = sys.argv[1:]
    if argv:
        if argv[0] != "--report" or len(argv) not in (1, 3) or (len(argv) == 3 and argv[1] != "--base"):
            print("usage: gate_on_stop.py --report [--base <rev>]  (with no arguments: the SubagentStop hook)",
                  file=sys.stderr)
            return 2
        return report(Path.cwd().resolve(), argv[2] if len(argv) == 3 else "HEAD")
    try:
        event = json.loads(sys.stdin.read())
        if not isinstance(event, dict) or "cwd" not in event:
            raise ValueError("no cwd in the hook input")
        return gate(event)
    except Exception as exc:  # fail open, reported
        print(f"dev-team gate: error — {type(exc).__name__}: {exc}", file=sys.stderr)
        return 0


if __name__ == "__main__":
    sys.exit(main())
