#!/usr/bin/env python3
"""SubagentStop hook for `dev-team:implementer`: the implementer may not finish while its
section's mechanical checks are red.

Input: the hook JSON on stdin (`cwd`, `agent_id`, `agent_type`, `stop_hook_active`).

1. Scope: exit 0 unless `agent_type` is `dev-team:implementer` and `<cwd>/docs/architecture.md`
   exists.
2. Marker: `<cwd>/.dev-team/stop` whose first line is `blocked` or `spec-change` (the
   implementer writes it before returning either) is deleted with the counter; exit 0 with
   nothing run.
3. Counter: `${CLAUDE_PLUGIN_DATA}/gate/<agent_id>` (else `<cwd>/.dev-team/gate-attempts/
   <agent_id>`) holds the attempt number; this stop adds one.
4. The run's diff: `HEAD~1..HEAD` when `HEAD`'s body carries a `Dev-Team-Run:` trailer, plus
   the working tree, untracked files counted as added in full. Its paths map to sections
   through status.py's `section_for_path`, longest section path first; a path the `surface`
   section would take counts only once `docs/packages/<pkg>/design/surface.md` exists. No
   section: exit 0.
5. Checks, every one run: the Floor and Enforced rows of `docs/constraints.md` per package (a
   `repo` row once), else the Toolchain commands; Measured rows, printed and never failed on.
   A row whose every located failure (a `path:line` or `path::test` its output names) is in an
   intent-test file the run did not touch is ELSEWHERE, not FAIL: the implementer may never
   edit `tests/intent/`, so blocking on another section's red or unlinted intent tests only
   burns its attempts. The line stays in the record for the reviewer;
   each section's intent suite, a failure tolerated when its `Design §<n> <item>` docstring
   matches the `Clause:` of a `proposed` or `approved` deviation entry for the section; the
   Guarded grep of the diff, pardoned by an unexpired Exceptions row; `status.py --surface`
   for the `surface` section.
6. Every line goes to `<cwd>/.dev-team/gate/<pkg>/<section>.txt` for each section in the run,
   so the reviewer of a section reads that section's last record, whichever implementer ran
   after it.
7. No FAIL: delete the counter, exit 0. A FAIL before attempt 3: the FAIL lines to stderr,
   exit 2 (from attempt 2 naming `debugging-and-error-recovery`). Attempt 3: the FAIL lines to
   stderr, delete the counter, exit 0.
8. Malformed stdin or any exception: report it on stderr and exit 0 (fail open, reported).

By hand, `python3 gate_on_stop.py --report [--base <rev>]` from the repo root runs the same
checks of step 5 over the diff from `<rev>` (default `HEAD`) to the working tree, with no
counter and no marker, and writes the same per-section files with `report` where the attempt
goes.
It prints the file and exits 1 on a FAIL line, 2 on a bad argument. The pair skill runs it at
wrap-up, so the reviewer of hand-made code reads a gate record of that code, not of the last
implementer's.

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
TIMEOUT = 240

# Guarded items on added lines: (the name a FAIL line prints, pattern). .py files only, so a
# README that quotes one is not a hit.
ADDED = (
    ("# noqa", re.compile(r"#\s*noqa\b", re.I)),
    ("# type: ignore", re.compile(r"#\s*type:\s*ignore\b")),
    ("# pragma: no cover", re.compile(r"#\s*pragma:\s*no\s*cover\b")),
    ("@pytest.mark.skip", re.compile(r"@pytest\.mark\.skip")),
)
XFAIL = re.compile(r"xfail")
DECISION = re.compile(r"\bD\d+\b")

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


def _untracked() -> list[str]:
    raw = status.git("ls-files", "--others", "--exclude-standard", "-z") or ""
    return [p for p in raw.split("\0") if p]


def diff_paths(base: str) -> list[str]:
    """Every path the run touched: changed since base, staged or not, and untracked."""
    changed = (status.git("diff", "--name-only", "-z", base) or "").split("\0")
    return sorted({p for p in changed + _untracked() if p})


def diff_lines(base: str) -> list[tuple[str, str, int, str]]:
    """(path, '+' or '-', line number, text) for every added and removed line since base.

    Added lines carry their new line number, removed lines their old one. An untracked file
    counts as added in full.
    """
    out: list[tuple[str, str, int, str]] = []
    raw = status.git("diff", "-U0", "--no-color", "--no-ext-diff", base) or ""
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
    for rel in _untracked():
        try:
            text = (status.ROOT / rel).read_text()
        except (OSError, UnicodeDecodeError):
            continue
        out += [(rel, "+", i, t) for i, t in enumerate(text.splitlines(), 1)]
    return out


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


def _elsewhere(out: str, touched: set[str]) -> list[str]:
    """The intent-test directories a failure lies in, when every located file is an untouched
    intent test; else [] (the failure is the run's to fix, or cannot be placed)."""
    located = _located(out)
    if not located or any("/tests/intent/" not in f"/{p}" or p in touched for p in located):
        return []
    return sorted({re.sub(r"(^|.*/)(tests/intent/[^/]+)/.*$", r"\1\2/", p) for p in located})


def _row(label: str, cmd: str, code: int, out: str, touched: set[str]) -> str:
    if code == 0:
        return f"PASS {label}: {cmd}"
    where = _elsewhere(out, touched)
    if where:
        return (f"ELSEWHERE {label}: {cmd} exited {code}, every failure in intent tests this run may not "
                f"edit ({', '.join(where)}): {_tail(out)}")
    return f"FAIL {label}: {cmd} exited {code}: {_tail(out)}"


def check_rows(pkgs: list[str], touched: set[str] | None = None) -> list[str]:
    """Floor and Enforced rows as PASS/FAIL/ELSEWHERE, Measured rows as MEASURED; else the Toolchain."""
    touched = touched or set()
    lines: list[str] = []
    seen: set[str] = set()
    if (status.DOCS / "constraints.md").exists():
        for pkg in pkgs:
            for heading, dim, cmd, scope in status.constraints_rows(pkg):
                key = f"repo {heading} {dim}" if scope.startswith("repo") else cmd
                if key in seen:
                    continue
                seen.add(key)
                code, out = _run(cmd, status.ROOT)
                what = dim or cmd
                if heading == "Measured":
                    last = [ln for ln in out.strip().splitlines() if ln.strip()]
                    lines.append(f"MEASURED {what}: {last[-1].strip() if last else 'no output'}")
                else:
                    lines.append(_row(f"{what} ({pkg})", cmd, code, out, touched))
        return lines
    for pkg in pkgs:
        for cmd in status.toolchain_commands():
            cmd = cmd.replace("<pkg>", pkg)
            if cmd in seen:
                continue
            seen.add(cmd)
            code, out = _run(cmd, status.ROOT)
            lines.append(_row("toolchain", cmd, code, out, touched))
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


def check_guarded(base: str, paths: list[str]) -> list[str]:
    exceptions = status.exceptions_rows()
    today = dt.date.today()
    lines = diff_lines(base)
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
        before = status.git("show", f"{base}:docs/constraints.md") if base != EMPTY_TREE else None
        after_file = status.DOCS / "constraints.md"
        if before and after_file.exists():
            old, new = _thresholds(before), _thresholds(after_file.read_text())
            for name, nums in old.items():
                if name in new and any(b < a for a, b in zip(nums, new[name])):
                    hits.append((f"lowered threshold {name}", "docs/constraints.md", 0))
    out = []
    for item, path, n in hits:
        if _pardoned(item, path, exceptions, today):
            out.append(f"PASS guarded {item} at {path}:{n} (Exceptions row)")
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


def run_checks(base: str | None) -> tuple[list[tuple[str, str]], list[str]]:
    """(sections in the diff since base, one line per check); no sections, no checks."""
    paths = diff_paths(base) if base else []
    targets = gated_sections(paths)
    if not targets or base is None:
        return targets, []
    pkgs = sorted({pkg for pkg, _ in targets})
    lines = check_rows(pkgs, set(paths))
    for pkg, section in targets:
        lines += check_intent(pkg, section)
    lines += check_guarded(base, paths)
    for pkg in sorted({pkg for pkg, section in targets if section == "surface"}):
        lines += check_surface(pkg)
    return targets, lines


def write_records(cwd: Path, targets: list[tuple[str, str]], text: str) -> list[Path]:
    """The record, once per section in the run: `.dev-team/gate/<pkg>/<section>.txt`."""
    out = []
    for pkg, section in targets:
        path = cwd / ".dev-team" / "gate" / pkg / f"{section}.txt"
        path.parent.mkdir(parents=True, exist_ok=True)
        path.write_text(text)
        out.append(path)
    return out


def _outcome_note(lines: list[str]) -> str:
    n = sum(1 for ln in lines if ln.startswith("ELSEWHERE"))
    return f" ({n} failing check{'s' * (n != 1)} elsewhere)" if n else ""


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
    targets, lines = run_checks(base)
    if not targets:
        print(f"dev-team gate: no section in the diff since {base}", file=sys.stderr)
        return 0
    fails = [ln for ln in lines if ln.startswith("FAIL")]
    names = ", ".join(f"{p}/{s}" for p, s in targets)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    outcome = ("result: pass" + _outcome_note(lines) if not fails
               else f"result: fail ({len(fails)} failure{'s' * (len(fails) != 1)}, report since {base})")
    text = "\n".join([f"dev-team gate — report — {stamp} — sections {names}", *lines, outcome]) + "\n"
    write_records(cwd, targets, text)
    print(text, end="")
    return 1 if fails else 0


def gate(event: dict) -> int:
    cwd = Path(event["cwd"]).resolve()
    if event.get("agent_type") != AGENT or not (cwd / "docs" / "architecture.md").exists():
        return 0
    counter = _counter(cwd, str(event.get("agent_id") or ""))
    marker = cwd / ".dev-team" / "stop"
    if marker.exists():
        first = (marker.read_text().strip().splitlines() or [""])[0].strip().lower()
        if first in MARKER_REASONS:
            marker.unlink()
            _clear(counter)
            return 0
    try:
        n = int(counter.read_text().strip()) + 1
    except (OSError, ValueError):
        n = 1
    counter.parent.mkdir(parents=True, exist_ok=True)
    counter.write_text(f"{n}\n")

    status.set_root(cwd)
    base = _base()
    targets, lines = run_checks(base)
    if not targets:
        _clear(counter)
        print("dev-team gate: no section in this run's diff", file=sys.stderr)
        return 0
    fails = [ln for ln in lines if ln.startswith("FAIL")]

    names = ", ".join(f"{p}/{s}" for p, s in targets)
    stamp = dt.datetime.now().strftime("%Y-%m-%d %H:%M:%S")
    if not fails:
        outcome = "result: pass" + _outcome_note(lines)
    elif n < MAX_ATTEMPTS:
        outcome = f"result: not done (attempt {n} of {MAX_ATTEMPTS})"
    else:
        outcome = f"result: letting the run stop after {MAX_ATTEMPTS} attempts with {len(fails)} failure{'s' * (len(fails) != 1)}"
    records = write_records(cwd, targets, "\n".join(
        [f"dev-team gate — attempt {n} — {stamp} — sections {names}", *lines, outcome]) + "\n")
    where = ", ".join(p.relative_to(cwd).as_posix() for p in records)

    if not fails:
        _clear(counter)
        return 0
    if n < MAX_ATTEMPTS:
        msg = [f"dev-team gate: not done — fix these, stage the fix, `git commit --amend --no-edit -- <paths>`, "
               f"and finish again (attempt {n} of {MAX_ATTEMPTS}):", *fails]
        if n == 2:
            msg.append("Two attempts: invoke `debugging-and-error-recovery` with the Skill tool before the third.")
        msg.append("When you finish, send your full return message again, first line `Result:`, through "
                   "your hand-back tool if you have one (SubagentHandback): the caller receives the last "
                   "hand-back, not your last turn, so a report sent before this retry is stale."
                   + (" This is your last retry: the next finish ends the run whatever the checks find, so "
                      "if anything is still red, write `Gate: let through after 3 attempts`." if n == 2 else ""))
        print("\n".join(msg), file=sys.stderr)
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
