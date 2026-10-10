#!/usr/bin/env python3
"""Mechanical check of issues.py's ledger layout, settling and routing, with no model.

Builds a throwaway plugin, files one issue, fixes it, and walks it through held checks:
the ledger is `runs/audits/`, an issue is `verified` until three holds from three sessions,
`settled` after, collapsed to one line in INDEX.md, absent from `list --format brief`, and
unsettled by a later Found in line. Then `route`: a small selection is fix-issues' (exit 0);
more than six issues, more than three issues across more than three roles, or an issue that
recurred after two fixes is revise-plugin's (exit 3).

Usage: python3 check.py        (exit 0 when every check passes)
"""

import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPT = Path(__file__).resolve().parents[3] / "scripts" / "issues.py"
failed = 0


def run(root: Path, *args: str) -> str:
    r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(root), *args],
                       capture_output=True, text=True)
    if r.returncode:
        print(r.stderr, file=sys.stderr)
        raise SystemExit(f"issues.py {' '.join(args[:2])} exited {r.returncode}")
    return r.stdout.strip()


def route(root: Path, *args: str) -> str:
    """`route`'s line and exit code, as `<code> <line>`: 3 is an answer, not a failure."""
    r = subprocess.run([sys.executable, str(SCRIPT), "--dir", str(root), "route", *args],
                       capture_output=True, text=True)
    return f"{r.returncode} {r.stdout.strip()}"


def new(root: Path, applies: str) -> str:
    return run(root, "new", "--title", "t", "--fault", "agent", "--severity", "WARN", "--check",
               "scope", "--applies-to", applies, "--rule-file", "agents/w.md", "--rule-line", "3",
               "--rule-quote", "q", "--found-version", "1.0.0", "--found-session", "dddddddd",
               "--found-date", "2026-10-09", "--finding", "f", "--unit", "U01", "--step", "U01.S1",
               "--evidence", "e", "--report", "r.md", "--finding-id", "W1")


def expect(name: str, got: str, want: str) -> None:
    global failed
    ok = got == want
    failed += not ok
    print(("PASS " if ok else "FAIL ") + name + ("" if ok else f"\n     got  {got!r}\n     want {want!r}"))


def held(root: Path, session: str, date: str) -> None:
    run(root, "check-result", "TO-001", "--attempt", "1", "--verdict", "held", "--session", session,
        "--version", "1.0.0", "--date", date, "--unit", "U01", "--step", "U01.S1", "--evidence", "ok")


with tempfile.TemporaryDirectory() as tmp:
    root = Path(tmp) / "toy"
    (root / ".claude-plugin").mkdir(parents=True)
    (root / ".claude-plugin" / "plugin.json").write_text('{"name": "toy", "version": "1.0.0"}')
    run(root, "new", "--title", "t", "--fault", "agent", "--severity", "ERROR", "--check", "scope",
        "--applies-to", "agent:w", "--rule-file", "agents/w.md", "--rule-line", "3",
        "--rule-quote", "q", "--found-version", "1.0.0", "--found-session", "aaaaaaaa",
        "--found-date", "2026-10-01", "--finding", "f", "--unit", "U01", "--step", "U01.S1",
        "--evidence", "e", "--report", "runs/audits/reports/2026-10-01-aaaaaaaa.md",
        "--finding-id", "E1")
    expect("ledger is runs/audits/", str((root / "runs/audits/issues/TO-001.md").exists()), "True")
    expect("no audits/ at the plugin root", str((root / "audits").exists()), "False")
    expect("open before a fix", run(root, "status", "TO-001"), "open")
    run(root, "fix", "TO-001", "--commit", "abc1234", "--branch", "b", "--files", "f", "--evals", "none",
        "--verify", "watch agent:w; held when x; recurred when y")
    expect("brief line", run(root, "list", "--format", "brief"),
           "TO-001 · attempt 1 · commit abc1234 · fixed_in — · watch agent:w · held when x · recurred when y")
    for i, status in enumerate(["verified", "verified", "settled"], start=1):
        held(root, f"{i}bbbbbbb", f"2026-10-0{i + 1}")
        expect(f"status after hold {i}", run(root, "status", "TO-001"), status)
    expect("settled leaves the brief list", run(root, "list", "--status", "fixed,released,verified",
                                                "--format", "brief"), "none")
    index = (root / "runs/audits/INDEX.md").read_text()
    expect("settled is one line, not a row", str("| [TO-001]" in index) + str("1 settled" in index), "FalseTrue")
    run(root, "seen", "TO-001", "--session", "cccccccc", "--version", "1.0.0", "--date", "2026-10-09",
        "--unit", "U01", "--step", "U01.S2", "--evidence", "again", "--report", "r.md", "--finding-id", "E1")
    expect("a later Found in unsettles it", run(root, "status", "TO-001"), "verified")
    expect("ledger check", run(root, "check"), "ok: 1 issues")

    expect("route: one issue is fix-issues'", route(root, "TO-001"), "0 route: fix-issues · 1 issue · 1 role")
    expect("route: nothing selected", route(root, "--status", "wontfix"), "0 route: none · 0 issues")
    expect("route: an unknown id is a problem, exit 1", route(root, "TO-999")[:1], "1")
    wide = new(root, "agent:a, agent:toy:b, agent:c, driver:run, cross")
    expect("route: one issue naming four roles is still fix-issues'", route(root, "TO-001", wide),
           "0 route: fix-issues · 2 issues · 5 roles")
    for role in ["agent:a", "agent:b", "agent:c"]:
        new(root, role)
    expect("route: more than three issues across more than three roles", route(root, "--session", "dddddddd"),
           "3 route: revise-plugin · 4 issues across 4 roles (fix-issues takes 3): agent:a, agent:b, agent:c, driver:run")
    for _ in range(3):
        new(root, "agent:w")
    expect("route: six issues in one role is fix-issues'",
           route(root, "TO-001", "TO-003", "TO-006", "TO-007", "TO-008", "TO-003")[:19], "0 route: fix-issues")
    expect("route: more than six issues", route(root, "--status", "open").split(" · 7 issues across")[0],
           "3 route: revise-plugin · 7 issues (fix-issues takes 6)")
    for n, session in [(1, "eeeeeeee"), (2, "ffffffff")]:
        if n == 2:
            run(root, "fix", "TO-001", "--commit", "abc1235", "--branch", "b", "--files", "f",
                "--evals", "none", "--verify", "watch agent:w; held when x; recurred when y")
        run(root, "check-result", "TO-001", "--attempt", str(n), "--verdict", "recurred", "--session",
            session, "--version", "1.0.0", "--date", f"2026-10-1{n}", "--unit", "U01", "--step",
            "U01.S1", "--evidence", "again")
        expect(f"route: recurred after {n} fix{'es' if n > 1 else ''}", route(root, "TO-001"),
               ["0 route: fix-issues · 1 issue · 1 role",
                "3 route: revise-plugin · TO-001 recurred after 2 fixes"][n - 1])

print(f"{'FAILED' if failed else 'all passed'}")
sys.exit(1 if failed else 0)
