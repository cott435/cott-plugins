#!/usr/bin/env python3
"""Print where every package and section stands, derived from docs/ and the code.

Usage:  python3 status.py [pkg] [--gate]

Nothing here is written down by anyone; it is all derived: a package is planned when its
contract exists, built when every section has a README, shipped when interface.md exists. A
section is reviewed when its newest review's `Commit:` line names a commit after which no
commit touches the section's source, tests/unit/<section> or tests/intent/<section>. The
intent column is the tester's suite, run: `<pass>/<total>`, or `—` with no tests/intent/<section>.
`--gate` exits 1 when the named package fails /dev-team:finalize-package's preconditions.
"""

from __future__ import annotations

import datetime as dt
import os
import re
import subprocess
import sys
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


def changed_since(sha: str, *paths: Path) -> bool:
    """True when a commit after sha touches any of paths, or sha is not in this history."""
    if git("merge-base", "--is-ancestor", sha, "HEAD") is None:
        return True
    return bool(git("log", "--format=%H", f"{sha}..HEAD", "--", *map(str, paths)))


def latest_review(stem: str) -> tuple[dt.date | None, str, str | None]:
    """Newest docs/reviews/<date>-<stem>.md → (date, verdict, its Commit: sha or None)."""
    best: tuple[dt.date, Path] | None = None
    for f in (DOCS / "reviews").glob(f"*-{stem}.md"):
        m = re.match(r"(\d{4}-\d{2}-\d{2})-", f.name)
        if m:
            d = dt.date.fromisoformat(m.group(1))
            if best is None or d > best[0]:
                best = (d, f)
    if not best:
        return None, "", None
    text = best[1].read_text()
    v = re.search(r"^Verdict:\s*(.+)$", text, re.M)
    c = re.search(r"^Commit:\s*([0-9a-f]{7,40})\b", text, re.M)
    return best[0], (v.group(1).strip() if v else "?"), (c.group(1) if c else None)


def freshness(stem: str, *paths: Path) -> tuple[str, str]:
    """Review state of the code at paths → (state, column text).

    state is `reviewed` when the newest review has a Commit: line and no commit since it
    touches paths; `uncommitted` when paths have changes git does not hold; else `stale`.
    A review with no Commit: line is stale by definition — there is no mtime fallback.
    """
    rdate, verdict, rsha = latest_review(stem)
    tail = f"{rdate or '—'} {verdict} @{rsha[:7] if rsha else '—'}".replace("  ", " ")
    if uncommitted(*paths):
        return "uncommitted", "uncommitted"
    if rsha and last_commit(*paths) and not changed_since(rsha, *paths):
        return "reviewed", f"✓ {tail}"
    return "stale", f"· {tail}"


def open_followups(target: str) -> tuple[int, int]:
    """(open items addressed to target, of which review-sourced)."""
    f = DOCS / "followups.md"
    if not f.exists():
        return 0, 0
    total = crit = 0
    for line in f.read_text().splitlines():
        if line.startswith("- [ ]") and re.match(rf"- \[ \]\s*{re.escape(target)}\s*:", line):
            total += 1
            if "review " in line:
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
    passed = re.search(r"(\d+) passed", run.stdout)
    if not total:
        return "?"
    return f"{passed.group(1) if passed else 0}/{total.group(1)}"


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
    rows = table_rows((pdocs / "contract.md").read_text(), ("section", "path"))
    lines.append("  section              design  built  intent   reviewed-since-build             open followups  markers")
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
        mk = markers(spath)
        itxt = intent(pkg_path, sec)
        lines.append(f"  {sec:<20} {'✓' if design else '·':^6} {'✓' if built else '·':^6} {itxt:^7}  {rev_txt:<32} {fu:>3} ({crit} review)  {mk:>5}")
        if not built:
            fails.append(f"{pkg}/{sec}: no README (unbuilt)")
        elif state == "uncommitted":
            fails.append(f"{pkg}/{sec}: uncommitted changes")
        elif state != "reviewed":
            fails.append(f"{pkg}/{sec}: not reviewed since last build")
        if crit:
            fails.append(f"{pkg}/{sec}: {crit} open review-sourced follow-up(s)")
    sfu, _ = open_followups(f"{pkg}/surface")
    src = pkg_path / "src" / pkg
    surface_paths = [src / n for n in ("__init__.py", "pipelines", "pipelines.py", "cli.py", "cli")]
    _, prev = freshness(f"{pkg}-package", *surface_paths)
    lines.append(f"  surface: open followups {sfu}; package review {prev}")
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
    args = [a for a in sys.argv[1:] if not a.startswith("--")]
    gate = "--gate" in sys.argv
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
    if gate:
        print("\nfinalize gate:", "PASS" if not all_fails else "FAIL")
        for f in all_fails:
            print("  -", f)
        return 1 if all_fails else 0
    return 0


if __name__ == "__main__":
    sys.exit(main())
