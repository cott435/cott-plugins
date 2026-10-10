#!/usr/bin/env python3
"""Mechanical check of `scripts/phases.py` and the two hooks, with no model.

    python3 evals/fixtures/phases/check.py

Builds a throwaway git repo holding a two-skill plugin and a four-phase plan (overview,
ledger, edit list), walks the plan with `phases.py` as `run-phases` and `run-phase` would,
and pipes recorded events into `hooks/guard_agent.py` and `hooks/gate_stop.py`. Prints PASS
or FAIL per case and `<n>/<m> pass`; exits 1 on any FAIL.
"""
import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
PLUGIN_DEV = HERE.parents[2]
PHASES = PLUGIN_DEV / "scripts" / "phases.py"
GUARD = PLUGIN_DEV / "hooks" / "guard_agent.py"
GATE = PLUGIN_DEV / "hooks" / "gate_stop.py"
results = []

OVERVIEW = """# toy p — overview

## Phases

One commit per phase. Names are exact.

| Phase | Note | What it adds | Items | Must not touch | Depends on |
|---|---|---|---|---|---|
| 0 | 00-overview | the plan | — | — | spec |
| 1 | 01-greet | hello greets by name | E-001 | wave | 0 |
| 2 | 02-loud | hello shouts | E-002 | wave | 1 |
| 3 | 03-docs | the README; hooks matcher `Read|Glob|Grep` | E-003 | — | all |

## Evals by phase

Baseline `previous` is the branch point.

**Checkpoints:** 3

| Phase | ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|---|
| 1–3 | R*.a | mechanical | `check-contracts` | — | `contracts.yml` | PASS |

| Phase | ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|---|
| 1 | R1.1 | mechanical | `scripts/x.py` | — | — | exits 0 |
| 3 | R3.e1 | behavioral | hello | working tree only | `evals/sets/hello.json` 1 | default |

## Breaking changes

1. none
"""

LEDGER = """# toy p — progress

Branch `toy-p`. One row per phase.

| Phase | Note | Status | Commit | Eval log(s) | Notes for the next chat |
|---|---|---|---|---|---|
| 0 | 00 | done | (phase 0) | | none |
| 1 | 01 | todo | | | start here; `a|b` is one cell |
| 2 | 02 | todo | | | |
| 3 | 03 | todo | | | Ends with the bump proposal |

## Standing facts

- none
"""

EDITS = """# toy p — edits

## Edits

### E-001 hello greets by name
- files: skills/hello/SKILL.md:5
- mechanism: prose

### E-002 hello shouts
- files: skills/hello/SKILL.md:6, scripts/x.py
- mechanism: prose

### E-003 the README
- files: README.md
- mechanism: prose
"""


def case(name, ok, detail=""):
    results.append(bool(ok))
    print(f"{'PASS' if ok else 'FAIL'} {name}{'' if ok else ' — ' + str(detail)[:600]}")


def sh(*args, cwd, stdin=None):
    return subprocess.run([str(a) for a in args], cwd=cwd, input=stdin, capture_output=True, text=True)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="phases-check-"))
    repo = tmp / "repo"
    toy = repo / "toy"
    notes = toy / "site" / "notes" / "p"
    for d in (toy / ".claude-plugin", toy / "skills" / "hello", toy / "skills" / "wave",
              toy / "evals" / "sets", notes):
        d.mkdir(parents=True)
    (toy / ".claude-plugin" / "plugin.json").write_text('{"name": "toy", "version": "0.1.0"}\n')
    for s in ("hello", "wave"):
        (toy / "skills" / s / "SKILL.md").write_text(f"---\nname: {s}\n---\nSay {s}.\n")
        (toy / "evals" / "sets" / f"{s}.json").write_text(json.dumps(
            {"target": s, "target_path": f"skills/{s}/SKILL.md", "evals": []}))
    (toy / "evals" / "README.md").write_text("# Evals\n\n| Date | Subject | File |\n|---|---|---|\n")
    (toy / ".gitignore").write_text("evals/workspace/\n")
    (repo / "README.md").write_text("repo\n")
    (notes / "p-00-overview.md").write_text(OVERVIEW)
    (notes / "p-progress.md").write_text(LEDGER)
    (notes / "p-edits.md").write_text(EDITS)
    git = ("git", "-c", "user.name=t", "-c", "user.email=t@t")
    sh("git", "init", "-q", "-b", "main", cwd=repo)
    sh("git", "add", "-A", cwd=repo)
    sh(*git, "commit", "-qm", "toy p (phase 0): the plan", cwd=repo)
    sh("git", "checkout", "-qb", "toy-p", cwd=repo)
    sh("git", "config", "user.name", "t", cwd=repo)
    sh("git", "config", "user.email", "t@t", cwd=repo)

    def ph(*args):
        return sh(sys.executable, PHASES, *args, cwd=toy)

    ledger = lambda: (notes / "p-progress.md").read_text()
    mark = toy / "evals" / "workspace" / "run-phases" / "p" / "active.json"

    # next
    r = ph("next")
    case("next: the phase, its note, no behavioral evals, the count",
         r.returncode == 0 and r.stdout.strip() == "phase 1 · 01-greet · todo · no behavioral evals · 1 of 4 done", r.stdout)
    sh("git", "checkout", "-q", "main", cwd=repo)
    r = ph("next")
    case("next on another branch: exit 1, both branches named",
         r.returncode == 1 and "`main`" in r.stdout and "`toy-p`" in r.stdout, r.stdout)
    sh("git", "checkout", "-q", "toy-p", cwd=repo)
    (toy / "stray.txt").write_text("x")
    r = ph("next")
    case("next with a stray file: exit 1, the path listed", r.returncode == 1 and "toy/stray.txt" in r.stdout, r.stdout)
    (toy / "stray.txt").unlink()

    # brief
    r = ph("brief")
    case("brief: this phase's row and eval rows, the recurring row, not another phase's",
         r.returncode == 0 and "**Items:** E-001" in r.stdout and "| R1.1 |" in r.stdout
         and "| R*.a |" in r.stdout and "R3.e1" not in r.stdout and "02-loud" not in r.stdout
         and "start here; `a|b` is one cell" in r.stdout and "not one: mechanical rows only" in r.stdout
         and "toy p (phase 1): <what>" in r.stdout, r.stdout)
    case("brief: the overview's prose and pointers to its other sections, the phase marked as begun",
         "Names are exact." in r.stdout and "Breaking changes: `sed -n" in r.stdout
         and json.loads(mark.read_text())["phase"] == 1, r.stdout[-400:])

    # finish
    (toy / "skills" / "hello" / "SKILL.md").write_text("---\nname: hello\n---\nSay hello, by name.\n")
    r = ph("finish", "--what", "hello greets by name")
    case("finish with no note: exit 1, nothing committed",
         r.returncode == 1 and "no phase note at site/notes/p/p-01-greet.md" in r.stdout
         and "todo" in ledger().split("| 1 |")[1][:20], r.stdout)
    (notes / "p-01-greet.md").write_text("# 01 — greet\n")
    (toy / "evals" / "2026-01-01-greet.md").write_text("# greet\n")
    r = ph("finish", "--what", "hello greets by name", "--log", "evals/2026-01-01-greet.md")
    case("finish with a log the index does not list: exit 1",
         r.returncode == 1 and "evals/README.md has no row for 2026-01-01-greet.md" in r.stdout, r.stdout)
    with open(toy / "evals" / "README.md", "a") as f:
        f.write("| 2026-01-01 | greet | [2026-01-01-greet.md](2026-01-01-greet.md) |\n")
    (repo / "README.md").write_text("repo, edited\n")
    r = ph("finish", "--what", "hello greets by name", "--log", "evals/2026-01-01-greet.md")
    case("finish with a change outside the plugin: exit 1 until --also names it",
         r.returncode == 1 and "not named with --also: README.md" in r.stdout, r.stdout)
    r = ph("finish", "--what", "hello greets by name", "--log", "evals/2026-01-01-greet.md",
           "--also", "README.md", "--notes", "phase 2 may shout", "--trailer", "Co-Authored-By: T <t@t>")
    log = sh("git", "log", "-1", "--format=%s%n%b", cwd=repo).stdout
    row0, row1 = [l for l in ledger().split("\n") if l.startswith(("| 0 |", "| 1 |"))]
    case("finish: one commit with the subject and trailer, a clean tree, the mark gone",
         r.returncode == 0 and log.startswith("toy p (phase 1): hello greets by name") and "Co-Authored-By: T" in log
         and not sh("git", "status", "--porcelain", cwd=repo).stdout and not mark.exists()
         and "next: phase 2" in r.stdout, r.stdout + log)
    case("finish: the row is done with its log and notes; phase 0's cell is its SHA",
         "| done | (phase 1) | `2026-01-01-greet.md` | phase 2 may shout |" in row1
         and "(phase 0)" not in row0 and "| done |" in row0, row0 + row1)

    # check
    r = ph("check", "1")
    case("check 1: exit 0 and the commit", r.returncode == 0 and "phase 1 committed:" in r.stdout, r.stdout)
    r = ph("check", "2")
    case("check 2: exit 1, the commit and the row named",
         r.returncode == 1 and "not a commit starting `toy p (phase 2):`" in r.stdout and "is `todo`" in r.stdout, r.stdout)

    # the stop gate, around a phase committed by hand
    event = lambda **kw: json.dumps(dict({"cwd": str(toy), "hook_event_name": "Stop"}, **kw))
    r = sh(sys.executable, GATE, cwd=tmp, stdin=event())
    case("gate: no phase begun, exit 0", r.returncode == 0 and not r.stderr, r.stderr)
    ph("brief")
    (toy / "skills" / "hello" / "SKILL.md").write_text("---\nname: hello\n---\nSAY HELLO, BY NAME.\n")
    r = sh(sys.executable, GATE, cwd=tmp, stdin=event())
    case("gate: a phase begun and not committed (a stop for a question), exit 0", r.returncode == 0, r.stderr)
    sh("git", "add", "-A", cwd=repo)
    sh(*git, "commit", "-qm", "toy p (phase 2): by hand", cwd=repo)
    r = sh(sys.executable, GATE, cwd=tmp, stdin=event())
    case("gate: the phase committed by hand with its row not done, exit 2 with the reason",
         r.returncode == 2 and "is `todo`, not `done`" in r.stderr and "finish p --what" in r.stderr, r.stderr)
    r = sh(sys.executable, GATE, cwd=tmp, stdin=event(stop_hook_active=True))
    case("gate: the second stop is let through", r.returncode == 0, r.stderr)
    r = sh(sys.executable, GATE, cwd=tmp, stdin=event(cwd=str(tmp)))
    case("gate: outside a plugin, exit 0", r.returncode == 0 and not r.stderr, r.stderr)
    r = sh(sys.executable, GATE, cwd=tmp, stdin="not json")
    case("gate: an unreadable event, exit 0 with the reason", r.returncode == 0 and "allowing" in r.stderr, r.stderr)
    (notes / "p-02-loud.md").write_text("# 02 — loud\n")
    r = ph("finish", "--what", "hello shouts")
    g = sh(sys.executable, GATE, cwd=tmp, stdin=event())
    case("finish after the hand commit: the phase stands and the gate is quiet",
         r.returncode == 0 and ph("check", "2").returncode == 0 and g.returncode == 0 and not mark.exists(), r.stdout + g.stderr)

    # a checkpoint phase
    r = ph("next")
    case("next: phase 3 is a checkpoint", "phase 3 · 03-docs · todo · checkpoint · 3 of 4 done" in r.stdout, r.stdout)
    (notes / "p-03-docs.md").write_text("# 03 — docs\n")
    r = ph("finish", "--what", "docs")
    case("finish at a checkpoint with a behavioral row not run: exit 1 naming the row",
         r.returncode == 1 and "row R3.e1 (hello) has no --iteration" in r.stdout, r.stdout)
    it = toy / "evals" / "workspace" / "hello" / "iteration-1"
    run = it / "eval-1-x" / "with_skill" / "run-1"
    run.mkdir(parents=True)
    r = ph("finish", "--what", "docs", "--iteration", "evals/workspace/hello/iteration-1")
    case("finish with an iteration that has no report: exit 1", r.returncode == 1 and "no report.md" in r.stdout, r.stdout)
    (it / "report.md").write_text("# hello iteration-1\n")
    (run / "not-run.json").write_text("{}")
    r = ph("finish", "--what", "docs", "--iteration", "evals/workspace/hello/iteration-1")
    case("finish with a run not run: exit 1 naming it",
         r.returncode == 1 and "eval-1-x/with_skill/run-1 was not run or not graded" in r.stdout, r.stdout)
    (run / "not-run.json").unlink()
    (run / "grading.json").write_text(json.dumps({"summary": {"passed": 3, "total": 4}}))
    (run / "timing.json").write_text(json.dumps({"total_tokens": 1500000}))
    r = ph("finish", "--what", "docs", "--iteration", "evals/workspace/hello/iteration-1")
    case("finish at the checkpoint with its iteration: committed, the plan done",
         r.returncode == 0 and "next: none" in r.stdout
         and "`evals/workspace/hello/iteration-1`" in ledger(), r.stdout)
    r = ph("next")
    case("next when every phase is done: exit 3", r.returncode == 3 and "plan done: 4 of 4" in r.stdout, r.stdout)
    r = ph("status")
    case("status: one line per phase, the checkpoint marked with its pass count and tokens",
         r.returncode == 0 and "[checkpoint]  evals 3/4, 1.5M tokens" in r.stdout
         and "4 of 4 phases done; evals so far 1.5M tokens" in r.stdout and r.stdout.count("done") >= 5, r.stdout)

    # touch and plan-check
    r = ph("touch")
    lines = {l.split("\t")[0]: l for l in r.stdout.splitlines()}
    case("touch: hello last touched in 2, its evals at 3; wave untouched",
         "last touched: 2\tevals at: 3\ttouched in: 1, 2" in lines.get("hello", "")
         and "last touched: —" in lines.get("wave", ""), r.stdout)
    r = ph("plan-check")
    case("plan-check: ok on the plan as written", r.returncode == 0 and r.stdout.strip().endswith("checkpoints 3"), r.stdout)
    ov = notes / "p-00-overview.md"
    ov.write_text(OVERVIEW.replace("| 3 | R3.e1 |", "| 1 | R3.e1 |"))
    r = ph("plan-check")
    case("plan-check: a behavioral row outside a checkpoint is a FAIL; a later touch is a warning",
         r.returncode == 1 and "FAIL row R3.e1: a behavioral row in phase 1, which is not a checkpoint" in r.stdout
         and "warning: row R3.e1: the edit list has hello touched again in phase 2" in r.stdout, r.stdout)
    ov.write_text(OVERVIEW.replace("**Checkpoints:** 3", "**Checkpoints:** 2"))
    r = ph("plan-check")
    case("plan-check: the last phase must be a checkpoint",
         r.returncode == 1 and "the last phase (3) is not a checkpoint" in r.stdout, r.stdout)
    ov.write_text(OVERVIEW.replace("**Checkpoints:** 3\n", ""))
    r = ph("plan-check")
    case("plan-check: no checkpoints named is a FAIL", r.returncode == 1 and "names no checkpoints" in r.stdout, r.stdout)

    # the Agent guard
    def guard(prompt):
        return sh(sys.executable, GUARD, cwd=tmp, stdin=json.dumps({"tool_name": "Agent", "tool_input": {"prompt": prompt}}))
    executor = f"You are testing `hello` by executing it. Keep `{run}/transcript.md`: each step."
    (it / "manifest.json").write_text(json.dumps({"runs": []}))
    r = guard(executor)
    case("guard: an executor spawned for a runner's iteration, exit 2 with the command to run",
         r.returncode == 2 and f"eval_workspace.py run {it}" in r.stderr, r.stderr)
    r = guard(f"Read `/x/agents/grader.md` and follow it. transcript_path: `{run}/transcript.md`.")
    case("guard: a grader the same", r.returncode == 2, r.stderr)
    (it / "manifest.json").write_text(json.dumps({"runs": [], "by_hand": True}))
    r = guard(executor)
    case("guard: the iteration laid out --by-hand, exit 0", r.returncode == 0 and not r.stderr, r.stderr)
    (it / "manifest.json").write_text(json.dumps({"runs": []}))
    r = guard("Survey the repo and report the three largest files.")
    case("guard: any other spawn, exit 0", r.returncode == 0 and not r.stderr, r.stderr)
    r = guard(f"Compare `{it}/eval-1-x/blind/A` and B as comparator.md says.")
    case("guard: a blind comparator, exit 0", r.returncode == 0, r.stderr)
    r = sh(sys.executable, GUARD, cwd=tmp, stdin="not json")
    case("guard: an unreadable event, exit 0 with the reason", r.returncode == 0 and "allowing" in r.stderr, r.stderr)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{sum(results)}/{len(results)} pass")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
