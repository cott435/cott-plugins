#!/usr/bin/env python3
"""Print where every package and section stands, derived from docs/ and the code.

Usage:  python3 status.py [pkg] [--gate] [--plan-gate <pkg>] [--run-gate] [--plan-rounds]

Nothing here is written down by anyone; it is all derived: a package is planned when its
contract exists, built when every section has a README, shipped when interface.md exists. A
section is reviewed when its newest review's (`<date>-<pkg>-<section>[-<n>].md`) `Commit:`
line names a commit after which no commit touches the section's source, tests/unit/<section>
or tests/intent/<section>. The
intent column is the tester's suite, run: `<pass>/<total>`, or `—` with no tests/intent/<section>.
`--gate` exits 1 when the named package fails /dev-team:finalize-package's preconditions.
`--plan-gate <pkg>` exits 1 unless the package's plan is complete, reviewed by
/dev-team:review-plan since its last change, approved, and carries no open plan finding and no
open decision without an assumption; it also prints the plan's round count — consecutive
`request changes` plan reviews since the last approving one — which /dev-team:review-plan and
/dev-team:run-package read to stop a plan-and-review loop that is not converging. `<pkg> --run-gate` exits 1 unless /dev-team:run-package may
start on pkg: a feature branch, a clean tree (git-workflow-and-versioning's Baseline
exemptions), contract.md and integration.md present, and either a spine-only plan (mode: spine)
or a plan that passes --plan-gate (mode: full) — or, once interface.md exists, mode: full with no
plan check. When docs/constraints.md exists, every package shows how
many of its Floor and Enforced rows fail, and `--gate` fails on each one that does.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import shlex
import subprocess
import sys
import tempfile
from pathlib import Path

ROOT = Path.cwd()
DOCS = ROOT / "docs"


def table_rows(md: str, must_have: tuple[str, ...]) -> list[dict[str, str]]:
    """Return the rows of the first markdown table whose header contains every name in must_have."""
    lines = md.splitlines()
    for i, line in enumerate(lines):
        if not line.startswith("|"):
            continue
        header = [c.strip().lower() for c in line.strip("|").split("|")]
        if all(any(m in h for h in header) for m in must_have) and i + 1 < len(lines) and set(lines[i + 1].replace("|", "").strip()) <= set("-: "):
            rows = []
            for row in lines[i + 2:]:
                if not row.startswith("|"):
                    break
                cells = [c.strip() for c in row.strip("|").split("|")]
                rows.append({h: (cells[k] if k < len(cells) else "") for k, h in enumerate(header)})
            return rows
    return []


def col(row: dict[str, str], name: str) -> str:
    """Fetch a cell by a loose header match, stripping backticks."""
    for h, v in row.items():
        if name in h:
            return v.strip("`* ")
    return ""


def git(*args: str) -> str | None:
    """Run a git command in the repo root; its stripped stdout, or None when git fails."""
    try:
        out = subprocess.run(["git", *args], capture_output=True, text=True, cwd=ROOT)
    except OSError:
        return None
    return out.stdout.strip() if out.returncode == 0 else None


def last_commit(*paths: Path) -> str | None:
    """Full SHA of the newest commit touching any of paths; None when not a repo or none does."""
    return git("log", "-1", "--format=%H", "--", *map(str, paths)) or None


def uncommitted(*paths: Path) -> bool:
    """True when any of paths has staged, unstaged or untracked changes."""
    return bool(git("status", "--porcelain", "--", *map(str, paths)))


def changed_since(sha: str, *paths: Path, ignore_runs: tuple[str, ...] = ()) -> bool:
    """True when a commit after sha touches any of paths, or sha is not in this history.

    A commit whose `Dev-Team-Run:` trailer names a run in ignore_runs does not count. That is
    how a plan stays reviewed across `/dev-team:sync-design`, which appends **As shipped** to
    every design of a package the plan review already passed: the designs it edits are what
    shipped, not a new plan to review. A commit that touches paths *and* other work is not
    exempt — the trailer is one run's own files.
    """
    if git("merge-base", "--is-ancestor", sha, "HEAD") is None:
        return True
    log = git("log", "--format=%H%x1f%B%x1e", f"{sha}..HEAD", "--", *map(str, paths)) or ""
    for entry in (e for e in log.split("\x1e") if e.strip()):
        head, _, body = entry.strip().partition("\x1f")
        run = re.search(r"^Dev-Team-Run:\s*(\S+)", body, re.M)
        if not (run and run.group(1) in ignore_runs):
            return bool(head)
    return False


def latest_review(stem: str) -> tuple[dt.date | None, str, str | None]:
    """Newest docs/reviews/<date>-<stem>[-<n>].md → (date, verdict, its Commit: sha or None).

    A second review on the same day is `<date>-<stem>-2.md`, a third `-3`, and so on; the
    highest suffix on the newest date wins.
    """
    best: tuple[dt.date, int, Path] | None = None
    pattern = re.compile(rf"(\d{{4}}-\d{{2}}-\d{{2}})-{re.escape(stem)}(?:-(\d+))?\.md")
    for f in (DOCS / "reviews").glob(f"*-{stem}*.md"):
        m = pattern.fullmatch(f.name)
        if m:
            key = (dt.date.fromisoformat(m.group(1)), int(m.group(2) or 1), f)
            if best is None or key[:2] > best[:2]:
                best = key
    if not best:
        return None, "", None
    text = best[2].read_text()
    v = re.search(r"^Verdict:\s*(.+)$", text, re.M)
    c = re.search(r"^Commit:\s*([0-9a-f]{7,40})\b", text, re.M)
    return best[0], (v.group(1).strip() if v else "?"), (c.group(1) if c else None)


def review_reports(stem: str) -> list[tuple[dt.date, int, Path]]:
    """Every docs/reviews/<date>-<stem>[-<n>].md, oldest first — (date, suffix, path)."""
    pattern = re.compile(rf"(\d{{4}}-\d{{2}}-\d{{2}})-{re.escape(stem)}(?:-(\d+))?\.md")
    out = []
    for f in (DOCS / "reviews").glob(f"*-{stem}*.md"):
        m = pattern.fullmatch(f.name)
        if m:
            out.append((dt.date.fromisoformat(m.group(1)), int(m.group(2) or 1), f))
    return sorted(out, key=lambda t: t[:2])


def plan_rounds(pkg: str) -> int:
    """Consecutive `request changes` plan reviews since the last approving one, newest first.

    Nothing writes this down: it is the count of reports the current plan-and-review loop has
    produced. 0 when the newest plan review approves, or there is none. /dev-team:review-plan
    numbers its report from it (`Round: <n+1>`) and stops the loop at the cap it states.
    """
    n = 0
    for _, _, f in reversed(review_reports(f"{pkg}-plan")):
        v = re.search(r"^Verdict:\s*(.+)$", f.read_text(), re.M)
        if v and v.group(1).strip().lower() in ("approve", "approve with fixes"):
            break
        n += 1
    return n


def freshness(stem: str, *paths: Path, ignore_runs: tuple[str, ...] = ()) -> tuple[str, str]:
    """Review state of the code at paths → (state, column text).

    state is `reviewed` when the newest review has a Commit: line and no commit since it
    touches paths; `uncommitted` when paths have changes git does not hold; else `stale`.
    A review with no Commit: line is stale by definition — there is no mtime fallback.
    ignore_runs names `Dev-Team-Run:` runs whose commits do not make a review stale.
    """
    rdate, verdict, rsha = latest_review(stem)
    tail = f"{rdate or '—'} {verdict} @{rsha[:7] if rsha else '—'}".replace("  ", " ")
    if uncommitted(*paths):
        return "uncommitted", "uncommitted"
    if rsha and last_commit(*paths) and not changed_since(rsha, *paths, ignore_runs=ignore_runs):
        return "reviewed", f"✓ {tail}"
    return "stale", f"· {tail}"


def open_followups(target: str) -> tuple[int, int]:
    """(open items addressed to target, of which review-sourced)."""
    f = DOCS / "followups.md"
    if not f.exists():
        return 0, 0
    total = crit = 0
    # An entry is its `- [ ]` line plus the indented lines that wrap it; `review ` may be on any.
    for entry in re.split(r"\n(?=\S)", f.read_text()):
        if re.match(rf"- \[ \]\s*{re.escape(target)}\s*:", entry):
            total += 1
            if "review " in entry:
                crit += 1
    return total, crit


def intent(pkg_path: Path, sec: str) -> str:
    """Pass/total of tests/intent/<sec> under pkg_path, from a collect and a run; `—` when absent."""
    tree = pkg_path / "tests" / "intent" / sec
    if not tree.is_dir():
        return "—"
    # uv when the repo is a uv project, else the interpreter on PATH; from the root, so the
    # repo's own pytest config (pythonpath, rootdir) applies. No bytecode and no cache: a
    # status run that left files behind would read as uncommitted changes on the next one.
    runner = ["uv", "run", "pytest"] if (ROOT / "uv.lock").exists() else ["python3", "-m", "pytest"]
    cmd = [*runner, str(tree.relative_to(ROOT)), "-q", "-p", "no:cacheprovider"]
    env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1"}
    try:
        co = subprocess.run([*cmd, "--co"], capture_output=True, text=True, cwd=ROOT, env=env)
        run = subprocess.run(cmd, capture_output=True, text=True, cwd=ROOT, env=env)
    except OSError:
        return "?"
    total = re.search(r"(\d+) tests? collected", co.stdout)
    if not total:
        return "?"
    # Not failing = total less failed and errors: an xfail is the tester's mark for a decision
    # still open on its assumption, and counts as holding.
    bad = sum(int(n) for n in re.findall(r"(\d+) (?:failed|errors?)\b", run.stdout))
    return f"{int(total.group(1)) - bad}/{total.group(1)}"


def spine(pdocs: Path) -> str | None:
    """The spine section when integration.md's **Spine** item or heading reads `spine only`, else None."""
    f = pdocs / "integration.md"
    if not f.exists():
        return None
    lines = f.read_text().splitlines()
    for i, line in enumerate(lines):
        if re.match(r"\s*(#+\s*Spine\b|(\d+\.\s*)?\*\*Spine\*\*)", line):
            block = [line]
            for nxt in lines[i + 1:]:
                if re.match(r"\s*(#|\d+\.\s*\*\*)", nxt):
                    break
                block.append(nxt)
            text = "\n".join(block)
            if "spine only" not in text.lower():
                return None
            sec = re.search(r"^\W*Section:\W*([\w-]+)", text, re.M)
            return sec.group(1) if sec else "?"
    return None


def spine_only(pdocs: Path) -> bool:
    """True when integration.md's **Spine** item or heading reads `spine only` before the next one."""
    return spine(pdocs) is not None


def blocking_decisions(pkg: str) -> list[str]:
    """D<n> that are open, have no assumption, and bind repo, pkg, or a section of pkg."""
    dec = DOCS / "decisions.md"
    if not dec.exists():
        return []
    out = []
    for e in re.split(r"^## D", dec.read_text(), flags=re.M)[1:]:
        field = lambda k: (re.search(rf"^{k}:[ \t]*(.*)$", e, re.M) or [None, ""])[1].strip()
        scope = [t.strip().strip("`") for t in (field("Scope") or field("Sections")).split(",")]
        binds = any(t in ("repo", pkg) or t.startswith(f"{pkg}/") for t in scope)
        if binds and field("Status").lower() == "open" and not field("Assumption if unanswered"):
            out.append("D" + e.split()[0])
    return out


def plan_gate(pkg: str) -> list[str]:
    """Reasons /dev-team:run-package may not build pkg from its plan; empty when it may."""
    pdocs = DOCS / "packages" / pkg
    if spine_only(pdocs):
        return [f"{pkg}: plan is spine-only ({spine(pdocs)}) — build it, then re-run plan-package"]
    missing = [f"{n}.md" for n in ("contract", "integration", "surface") if not (pdocs / f"{n}.md").exists()]
    if missing:
        return [f"{pkg}: plan incomplete, missing {', '.join(missing)}"]
    fails = []
    _, verdict, _ = latest_review(f"{pkg}-plan")
    state, _ = freshness(f"{pkg}-plan", *plan_paths(pdocs), ignore_runs=PLAN_EXEMPT_RUNS)
    if state != "reviewed":
        fails.append(f"{pkg}: plan not reviewed since last change")
    elif verdict.lower() not in ("approve", "approve with fixes"):
        rounds = plan_rounds(pkg)
        # Round 3 or later is the reviewer's unconditional stop; the round-2 convergence test is
        # its own, in the report. The gate only says which command table row applies.
        tail = f" (round {rounds}; not converging — see the report's stop block)" if rounds >= 3 else f" (round {rounds})"
        fails.append(f"{pkg}: plan review verdict is {verdict}{tail}")
    _, crit = open_followups(f"{pkg}/plan")
    if crit:
        fails.append(f"{pkg}: {crit} open plan finding(s)")
    for d in blocking_decisions(pkg):
        fails.append(f"{pkg}: {d} is open with no assumption")
    return fails


# git-workflow-and-versioning §Project convention, Baseline: the files the user edits between runs,
# and agent memory, which agents write and nobody stages but the user.
BASELINE_EXEMPT = ("docs/decisions.md", "docs/brief.md", "docs/constraints.md")

# A plan review covers the plan: the package contract, every design, integration.md and
# surface.md. interface.md is what shipped, so finalize-package writing it leaves the plan
# review current, and sync-design appending **As shipped** to those designs does too.
PLAN_EXEMPT_RUNS = ("sync-design",)


def plan_paths(pdocs: Path) -> tuple[Path, ...]:
    """The documents a plan review covers, under docs/packages/<pkg>/."""
    return (pdocs / "contract.md", pdocs / "integration.md", pdocs / "surface.md", pdocs / "design")


def run_gate(pkg: str) -> tuple[str | None, list[str]]:
    """(mode, reasons) for /dev-team:run-package on pkg: mode `spine` or `full` when reasons is empty."""
    if git("rev-parse", "--is-inside-work-tree") is None:
        return None, ["not a git repository; `git init`, create a branch, and re-run"]
    fails = []
    branch = git("branch", "--show-current") or ""
    if branch in ("main", "master"):
        fails.append(f"on `{branch}`; create a feature branch and re-run")
    # -z: NUL-separated and unquoted, read unstripped — git() strips the leading status space
    # of the first entry. A rename or copy entry is followed by its source path, skipped.
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
        if path not in BASELINE_EXEMPT and not path.startswith(".claude/agent-memory/"):
            dirty.append(path)
    if dirty:
        fails.append(f"uncommitted changes outside the user-edited files: {', '.join(dirty)}")
    pdocs = DOCS / "packages" / pkg
    missing = [f"{n}.md" for n in ("contract", "integration") if not (pdocs / f"{n}.md").exists()]
    if missing:
        fails.append(f"{pkg}: missing {', '.join(missing)} — run /dev-team:plan-package {pkg}")
    if fails:
        return None, fails
    if spine_only(pdocs):
        return "spine", []
    if (pdocs / "interface.md").exists():
        # Shipped: finalize-package wrote interface.md and sync-design appends As shipped under
        # docs/packages/<pkg>/, so the plan review is stale by construction. The package review
        # is the gate now; the driver has only the close-out left to resume.
        return "full", []
    pfails = plan_gate(pkg)
    return (None, pfails) if pfails else ("full", [])


def constraints_rows(pkg: str) -> list[tuple[str, str, str]]:
    """(dimension, command, scope) for every Floor and Enforced row of docs/constraints.md, <pkg> filled in."""
    f = DOCS / "constraints.md"
    if not f.exists():
        return []
    text = f.read_text()
    out = []
    for heading, name_col in (("Floor", "check"), ("Enforced", "dimension")):
        m = re.search(rf"^##\s+{heading}\b.*?(?=^##\s|\Z)", text, re.M | re.S)
        for row in table_rows(m.group(0), ("command", "scope")) if m else []:
            cmd = col(row, "command")
            if cmd:
                out.append((col(row, name_col) or col(row, "dimension"), cmd.replace("<pkg>", pkg), col(row, "scope").lower() or "package"))
    return out


_constraint_results: dict[str, bool] = {}


def run_constraint(command: str) -> bool:
    """Run one constraints command from the repo root; True when it exits 0. Cached per command.

    No shell; a 10-minute timeout. Tool caches (pytest, coverage, mypy, ruff, bytecode) go to a
    temporary directory: a status run that left files behind would read as uncommitted changes.
    """
    if command in _constraint_results:
        return _constraint_results[command]
    with tempfile.TemporaryDirectory() as tmp:
        env = {**os.environ, "PYTHONDONTWRITEBYTECODE": "1", "COVERAGE_FILE": f"{tmp}/.coverage",
               "MYPY_CACHE_DIR": f"{tmp}/mypy", "RUFF_CACHE_DIR": f"{tmp}/ruff",
               "PYTEST_ADDOPTS": (os.environ.get("PYTEST_ADDOPTS", "") + " -p no:cacheprovider").strip()}
        try:
            ok = subprocess.run(shlex.split(command), capture_output=True, cwd=ROOT, env=env, timeout=600).returncode == 0
        except (OSError, subprocess.TimeoutExpired):
            ok = False
    _constraint_results[command] = ok
    return ok


def constraint_failures(pkg: str) -> tuple[int, list[str]]:
    """(rows run, one gate line per failing row) for pkg; (0, []) with no docs/constraints.md."""
    rows = constraints_rows(pkg)
    fails = [f"{pkg}: constraint {dim} FAIL ({cmd})" for dim, cmd, _ in rows if not run_constraint(cmd)]
    return len(rows), fails


def markers(path: Path) -> int:
    """Count TODO(decision ...) markers under a path."""
    if not path.exists():
        return 0
    return sum(len(re.findall(r"TODO\(decision", p.read_text(errors="ignore"))) for p in path.rglob("*.py"))


def packages() -> list[tuple[str, Path]]:
    arch = DOCS / "architecture.md"
    out: list[tuple[str, Path]] = []
    if arch.exists():
        for row in table_rows(arch.read_text(), ("package", "path")):
            name, path = col(row, "package"), col(row, "path")
            if name and not name.startswith("-"):
                out.append((name, ROOT / (path or ".")))
    if not out:
        out = [(d.name, ROOT / "packages" / d.name) for d in sorted((DOCS / "packages").glob("*")) if d.is_dir()]
    return out


def package_report(pkg: str, pkg_path: Path) -> tuple[list[str], list[str]]:
    """Lines to print and a list of finalize-gate failures."""
    pdocs = DOCS / "packages" / pkg
    have = {n: (pdocs / f"{n}.md").exists() for n in ("contract", "integration", "surface", "interface")}
    status = "shipped" if have["interface"] else ("planned" if have["contract"] else "unplanned")
    lines = [f"\n## {pkg}  —  {status}   " + "  ".join(f"{k}.md {'✓' if v else '·'}" for k, v in have.items())]
    fails: list[str] = []
    if not have["contract"]:
        return lines + ["  (no contract.md — run /dev-team:plan-package)"], [f"{pkg}: no contract.md"]
    if not have["surface"]:
        fails.append(f"{pkg}: no surface.md")
    pdate, pverdict, psha = latest_review(f"{pkg}-plan")
    pstate, _ = freshness(f"{pkg}-plan", *plan_paths(pdocs), ignore_runs=PLAN_EXEMPT_RUNS)
    ptail = f"{pdate} {pverdict} @{psha[:7] if psha else '—'}"
    if spine_only(pdocs):
        lines.append(f"  plan: spine only ({spine(pdocs)}) — build it, then re-run plan-package")
    else:
        rounds = plan_rounds(pkg)
        lines.append("  plan: " + ("unreviewed" if not pdate else f"reviewed {ptail}" if pstate == "reviewed" else f"{pstate} (last review {ptail})")
                     + (f"; {rounds} request-changes round(s) since last approve" if rounds else ""))
    rows = table_rows((pdocs / "contract.md").read_text(), ("section", "path"))
    lines.append("  section              design  built  intent   reviewed-since-build             open followups          markers")
    all_built = True
    for row in rows:
        sec = col(row, "section")
        if not sec:
            continue
        spath = ROOT / col(row, "path") if col(row, "path") else pkg_path / "src" / pkg / sec
        readme = spath / "README.md"
        design = (pdocs / "design" / f"{sec}.md").exists()
        built = readme.exists()
        all_built &= built
        tests = pkg_path / "tests"
        state, rev_txt = freshness(f"{pkg}-{sec}", spath, tests / "unit" / sec, tests / "intent" / sec)
        fu, crit = open_followups(f"{pkg}/{sec}")
        ifu, _ = open_followups(f"{pkg}/{sec}/intent")
        mk = markers(spath)
        itxt = intent(pkg_path, sec)
        lines.append(f"  {sec:<20} {'✓' if design else '·':^6} {'✓' if built else '·':^6} {itxt:^7}  {rev_txt:<32} {fu + ifu:>3} ({crit} review, {ifu} intent)  {mk:>5}")
        if not built:
            fails.append(f"{pkg}/{sec}: no README (unbuilt)")
        elif state == "uncommitted":
            fails.append(f"{pkg}/{sec}: uncommitted changes")
        elif state != "reviewed":
            fails.append(f"{pkg}/{sec}: not reviewed since last build")
        if crit:
            fails.append(f"{pkg}/{sec}: {crit} open review-sourced follow-up(s)")
        if ifu:
            fails.append(f"{pkg}/{sec}: {ifu} open follow-up(s) in tests/intent — run /dev-team:test-section {pkg}/{sec}")
    sfu, _ = open_followups(f"{pkg}/surface")
    src = pkg_path / "src" / pkg
    surface_paths = [src / n for n in ("__init__.py", "pipelines", "pipelines.py", "cli.py", "cli")]
    _, prev = freshness(f"{pkg}-package", *surface_paths)
    lines.append(f"  surface: open followups {sfu}; package review {prev}")
    if (DOCS / "constraints.md").exists() and not src.exists():
        lines.append(f"  constraints: {len(constraints_rows(pkg))} enforced, not run (no code)")
    elif (DOCS / "constraints.md").exists():
        n, cfails = constraint_failures(pkg)
        lines.append(f"  constraints: {n} enforced, {len(cfails)} failing")
        fails += cfails
    else:
        lines.append("  constraints: no docs/constraints.md")
    if all_built and status == "planned":
        lines[0] = lines[0].replace("planned", "built, not finalized")
    return lines, fails


def repo_report() -> list[str]:
    lines = ["\n## repo"]
    dec = DOCS / "decisions.md"
    if dec.exists():
        text = dec.read_text()
        entries = re.split(r"^## D", text, flags=re.M)[1:]
        opn = sum(1 for e in entries if re.search(r"^Status:\s*(open|deferred)", e, re.M))
        decided_unapplied = [e.split()[0] for e in entries if re.search(r"^Status:\s*decided", e, re.M) and not re.search(r"^Applied:\s*\S", e, re.M)]
        lines.append(f"  decisions: {len(entries)} total, {opn} open/deferred, decided without Applied: {', '.join('D' + d for d in decided_unapplied) or 'none'}")
    else:
        lines.append("  decisions: no ledger")
    plans = [p.parent.name for p in (DOCS / "plans").glob("*/integration.md")]
    synced = (DOCS / "plans" / "synced.md").read_text() if (DOCS / "plans" / "synced.md").exists() else ""
    unsynced = [s for s in plans if s not in synced]
    lines.append(f"  plans: {len(plans)} with integration.md, unsynced: {', '.join(unsynced) or 'none'}")
    fu = DOCS / "followups.md"
    if fu.exists():
        lines.append(f"  open followups: {sum(1 for l in fu.read_text().splitlines() if l.startswith('- [ ]'))}")
    return lines


def main() -> int:
    argv = sys.argv[1:]
    plan_pkg = None
    if "--plan-gate" in argv:
        i = argv.index("--plan-gate")
        if i + 1 >= len(argv) or argv[i + 1].startswith("--"):
            print("--plan-gate needs a package name")
            return 2
        plan_pkg = argv.pop(i + 1)
    args = [a for a in argv if not a.startswith("--")]
    if "--plan-rounds" in argv:
        # The reviewer's one question in plan mode; no package report, so no test or
        # constraint command runs.
        if not args:
            print("--plan-rounds needs a package name: status.py <pkg> --plan-rounds")
            return 2
        print(f"plan rounds since last approve: {plan_rounds(args[0])}")
        return 0
    gate = "--gate" in argv
    run = "--run-gate" in argv
    if run and not args:
        print("--run-gate needs a package name: status.py <pkg> --run-gate")
        return 2
    if plan_pkg and not args:
        args = [plan_pkg]
    only = args[0] if args else None
    if not DOCS.exists():
        print("no docs/ directory here — run from the repo root")
        return 2
    all_fails: list[str] = []
    for pkg, path in packages():
        if only and pkg != only:
            continue
        lines, fails = package_report(pkg, path)
        print("\n".join(lines))
        all_fails += fails
    if not only:
        print("\n".join(repo_report()))
    code = 0
    if plan_pkg:
        pfails = plan_gate(plan_pkg)
        print("\nplan gate:", "PASS" if not pfails else "FAIL")
        for f in pfails:
            print("  -", f)
        print(f"plan rounds since last approve: {plan_rounds(plan_pkg)}")
        code |= 1 if pfails else 0
    if run:
        mode, rfails = run_gate(only)
        print("\nrun gate:", f"PASS (mode: {mode})" if mode else "FAIL")
        for f in rfails:
            print("  -", f)
        code |= 0 if mode else 1
    if gate:
        print("\nfinalize gate:", "PASS" if not all_fails else "FAIL")
        for f in all_fails:
            print("  -", f)
        code |= 1 if all_fails else 0
    return code


if __name__ == "__main__":
    sys.exit(main())
