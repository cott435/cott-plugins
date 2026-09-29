#!/usr/bin/env python3
"""Pipe every recorded hook event into its script and check what the script did.

Usage:  python3 check.py [case ...]

Each case is `events/<case>.json`:

- `script`: `format`, `gate`, `guard` or `sync` (hooks/format_on_edit.py, gate_on_stop.py,
  guard_writes.py, sync_decisions.py).
- `repo`: `built` (build.py: one built section, one proposed deviation), `arch` (a directory
  holding only `docs/architecture.md`) or `plain` (an empty directory: out of scope).
- `setup`: `prior`, files committed just before the run's commit (so they are in the repo
  but not in the run's diff); `files` written into the repo (uncommitted unless `commit` names
  a message, which commits everything); `counter`, the gate's attempt count before this
  stop; and `stale_lock`, a name whose `.dev-team/locks/<name>/` is created with its mtime set
  1200 s back (a crashed holder's lock).
- `event`: the hook input as Claude Code sends it, `{cwd}` standing for the repo; or `raw`,
  stdin sent verbatim. `args`: command-line arguments, for the gate's `--report` mode and the
  sync hook's `--all`, which read no stdin.
- `env`: extra environment for the script (the gate's `DEV_TEAM_GATE_TIMEOUT` and
  `DEV_TEAM_GATE_BUDGET`, say).
- `expect`: `exit`; `stdout` (exact, stripped), `stdout_contains`; `stderr` (exact), `stderr_contains`, `stderr_lacks`, `stderr_startswith`;
  `file_equals`, `file_contains`, `file_lacks` (repo-relative); `absent` (paths that must not
  exist); `gate_contains`, `gate_lacks`, and `gate_only` (every line of the gate's record for
  `gate_section`, default `data/ingest`, at `.dev-team/gate/<pkg>/<section>.txt`, between the
  header and the `result:` line starts with one of these); `counter` (the attempt
  count after, `null` for no counter file).

The script runs with `CLAUDE_PLUGIN_ROOT` set to this plugin and `CLAUDE_PLUGIN_DATA` to a
temporary directory, exactly as hooks.json invokes it (`python3 <script>`). Prints PASS or
FAIL per case and exits 1 naming each failed case.
"""

from __future__ import annotations

import json
import os
import subprocess
import sys
import tempfile
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN = HERE.parents[2]
SCRIPTS = {"format": "format_on_edit.py", "gate": "gate_on_stop.py", "guard": "guard_writes.py",
           "sync": "sync_decisions.py"}
sys.path.insert(0, str(HERE))
import build  # noqa: E402

ARCH = "# Architecture\n\n## Packages\n\n| package | path | depends on | covers |\n|---|---|---|---|\n| data | packages/data | — | load trades |\n"


def _repo(kind: str, dest: Path) -> Path:
    if kind == "built":
        return build.build(dest)
    dest.mkdir(parents=True)
    if kind == "arch":
        (dest / "docs").mkdir()
        (dest / "docs" / "architecture.md").write_text(ARCH)
    return dest


def check(case: Path) -> list[str]:
    spec = json.loads(case.read_text())
    exp, setup = spec["expect"], spec.get("setup", {})
    with tempfile.TemporaryDirectory() as tmp:
        tmp_path = Path(tmp).resolve()
        repo = _repo(spec["repo"], tmp_path / "repo")
        data = tmp_path / "plugin-data"
        if "prior" in setup:  # slip a commit in under the run's: undo it, commit these, redo it
            git = ["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid"]
            msg = subprocess.run([*git, "log", "-1", "--format=%B"], cwd=repo, check=True,
                                 capture_output=True, text=True).stdout
            subprocess.run([*git, "reset", "-q", "--soft", "HEAD~1"], cwd=repo, check=True)
            for rel, text in setup["prior"].items():
                (repo / rel).parent.mkdir(parents=True, exist_ok=True)
                (repo / rel).write_text(text)
            subprocess.run([*git, "add", *setup["prior"]], cwd=repo, check=True)
            subprocess.run([*git, "commit", "-q", "-m", "fixture: before the run", "--", *setup["prior"]],
                           cwd=repo, check=True)
            subprocess.run([*git, "commit", "-q", "-m", msg], cwd=repo, check=True)
        for rel, text in setup.get("files", {}).items():
            (repo / rel).parent.mkdir(parents=True, exist_ok=True)
            (repo / rel).write_text(text)
        if "commit" in setup:
            subprocess.run(["git", "add", "-A"], cwd=repo, check=True)
            subprocess.run(["git", "-c", "user.name=fixture", "-c", "user.email=fixture@example.invalid",
                            "commit", "-q", "-m", setup["commit"]], cwd=repo, check=True)
        if "stale_lock" in setup:
            lock = repo / ".dev-team" / "locks" / setup["stale_lock"]
            lock.mkdir(parents=True)
            then = time.time() - 1200
            os.utime(lock, (then, then))
        event = spec.get("event")
        agent_id = (event or {}).get("agent_id", "")
        counter = data / "gate" / agent_id
        if "counter" in setup:
            counter.parent.mkdir(parents=True, exist_ok=True)
            counter.write_text(f"{setup['counter']}\n")
        stdin = spec["raw"] if "raw" in spec else "" if event is None else json.dumps(event).replace("{cwd}", str(repo))
        env = {**os.environ, "CLAUDE_PLUGIN_ROOT": str(PLUGIN), "CLAUDE_PLUGIN_DATA": str(data), **spec.get("env", {})}
        res = subprocess.run(["python3", str(PLUGIN / "hooks" / SCRIPTS[spec["script"]]), *spec.get("args", [])],
                             input=stdin, capture_output=True, text=True, cwd=repo, env=env)
        problems = []
        err = res.stderr
        if "exit" in exp and res.returncode != exp["exit"]:
            problems.append(f"exit {res.returncode}, expected {exp['exit']}")
        if "stderr" in exp and err.strip() != exp["stderr"]:
            problems.append(f"stderr {err.strip()!r}, expected {exp['stderr']!r}")
        if "stderr_startswith" in exp and not err.startswith(exp["stderr_startswith"]):
            problems.append(f"stderr does not start {exp['stderr_startswith']!r}")
        if "stdout" in exp and res.stdout.strip() != exp["stdout"]:
            problems.append(f"stdout {res.stdout.strip()!r}, expected {exp['stdout']!r}")
        problems += [f"stdout lacks {s!r}" for s in exp.get("stdout_contains", []) if s not in res.stdout]
        problems += [f"stderr lacks {s!r}" for s in exp.get("stderr_contains", []) if s not in err]
        problems += [f"stderr has {s!r}" for s in exp.get("stderr_lacks", []) if s in err]
        for rel, text in exp.get("file_equals", {}).items():
            if (repo / rel).read_text() != text:
                problems.append(f"{rel} changed:\n{(repo / rel).read_text()}")
        for rel, subs in exp.get("file_contains", {}).items():
            problems += [f"{rel} lacks {s!r}" for s in subs if s not in (repo / rel).read_text()]
        for rel, subs in exp.get("file_lacks", {}).items():
            problems += [f"{rel} has {s!r}" for s in subs if s in (repo / rel).read_text()]
        problems += [f"{rel} exists" for rel in exp.get("absent", []) if (repo / rel).exists()]
        gate_rel = f".dev-team/gate/{exp.get('gate_section', 'data/ingest')}.txt"
        gate_file = repo / gate_rel
        gate = gate_file.read_text() if gate_file.exists() else ""
        if any(k in exp for k in ("gate_contains", "gate_lacks", "gate_only")) and not gate:
            problems.append(f"no {gate_rel}")
        problems += [f"gate.txt lacks {s!r}" for s in exp.get("gate_contains", []) if s not in gate]
        problems += [f"gate.txt has {s!r}" for s in exp.get("gate_lacks", []) if s in gate]
        if "gate_only" in exp and gate:
            body = gate.strip().splitlines()[1:-1]
            problems += [f"gate.txt line {ln!r}" for ln in body if not ln.startswith(tuple(exp["gate_only"]))]
        if "counter" in exp:
            now = int(counter.read_text()) if agent_id and counter.exists() else None
            if now != exp["counter"]:
                problems.append(f"counter {now}, expected {exp['counter']}")
        if problems:
            problems.append("stderr:\n    " + err.strip().replace("\n", "\n    "))
            if gate:
                problems.append("gate.txt:\n    " + gate.strip().replace("\n", "\n    "))
    return problems


def main() -> int:
    events = HERE / "events"
    names = sys.argv[1:] or sorted(f.stem for f in events.glob("*.json"))
    failed = []
    for name in names:
        problems = check(events / f"{name}.json")
        print(f"{'PASS' if not problems else 'FAIL'}  {name}")
        for p in problems:
            print(f"      {p}")
        if problems:
            failed.append(name)
    print(f"\n{len(names) - len(failed)}/{len(names)} pass" + (f"; failed: {', '.join(failed)}" if failed else ""))
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
