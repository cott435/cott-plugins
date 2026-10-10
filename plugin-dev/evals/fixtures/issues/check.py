#!/usr/bin/env python3
"""Mechanical check of issues.py's ledger layout and settling, with no model.

Builds a throwaway plugin, files one issue, fixes it, and walks it through held checks:
the ledger is `runs/audits/`, an issue is `verified` until three holds from three sessions,
`settled` after, collapsed to one line in INDEX.md, absent from `list --format brief`, and
unsettled by a later Found in line.

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

print(f"{'FAILED' if failed else 'all passed'}")
sys.exit(1 if failed else 0)
