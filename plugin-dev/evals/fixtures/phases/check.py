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
EDITS_PY = PLUGIN_DEV / "scripts" / "edits.py"
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

**Init flags:** `--reuse-unhashed`

| Phase | ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|---|
| 1–3 | R*.a | mechanical | `check-contracts` | — | `contracts.yml` | PASS |

| Phase | ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|---|
| 1 | R1.1 | mechanical | `scripts/x.py` | — | — | exits 0 |
| 3 | R3.e1 | behavioral | hello | working tree only | `evals/sets/hello.json` 1, 3–4 | default |
| 3 | R3.e2 | behavioral | hello | previous | `evals/sets/hello.json` 5 | default, compared |

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


GIT = ("git", "-c", "user.name=t", "-c", "user.email=t@t")


def build(repo, overview):
    """A git repo at `repo` holding the toy plugin and its plan, on the plan's branch."""
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
    (toy / ".gitignore").write_text("evals/workspace/\nsite/docs/\nsite/_build/\n")
    (toy / "site" / "site.yml").write_text("# every key is optional\n")
    (repo / "README.md").write_text("repo\n")
    (notes / "p-00-overview.md").write_text(overview)
    (notes / "p-progress.md").write_text(LEDGER)
    (notes / "p-edits.md").write_text(EDITS)
    sh("git", "init", "-q", "-b", "main", cwd=repo)
    sh("git", "add", "-A", cwd=repo)
    sh(*GIT, "commit", "-qm", "toy p (phase 0): the plan", cwd=repo)
    sh("git", "checkout", "-qb", "toy-p", cwd=repo)
    sh("git", "config", "user.name", "t", cwd=repo)
    sh("git", "config", "user.email", "t@t", cwd=repo)
    return toy, notes


def checks_cases(tmp):
    """`checks`, and `finish` behind it, on a plan whose overview has a **Checks:** line."""
    repo = tmp / "checks-repo"
    toy, notes = build(repo, OVERVIEW.replace(
        "**Init flags:**", "**Checks:** `python3 scripts/x.py` · `python3 scripts/y.py`\n\n**Init flags:**"))
    (toy / "contracts.yml").write_text(
        "forbid:\n  - name: no skill says goodbye\n    pattern: 'goodbye'\n    files: ['skills/*/SKILL.md']\n")
    (toy / "scripts").mkdir()
    (toy / "scripts" / "x.py").write_text("print('PASS a')\nprint('2/2 pass')\n")
    (toy / "scripts" / "y.py").write_text(
        "import sys\nprint('PASS b')\nprint('FAIL c')\nprint('    the detail')\nprint('noise')\nsys.exit(1)\n")
    (notes / "p-01-greet.md").write_text("# 01 — greet\n")

    def ph(*args):
        return sh(sys.executable, PHASES, *args, cwd=toy)

    r = ph("brief")
    case("brief with a **Checks:** line: the one command, what it runs (no build-site before the last phase), the foreground timeout",
         f"{PHASES} checks p` runs `check-contracts`, `python3 scripts/x.py`, `python3 scripts/y.py` in one" in r.stdout
         and "`timeout: 600000`" in r.stdout and "`finish` refuses until `checks` has passed" in r.stdout, r.stdout)
    r = ph("finish", "--what", "greet")
    case("finish before checks: exit 1 with the command", r.returncode == 1
         and "checks have not passed on the tree as it stands" in r.stdout and "checks p`" in r.stdout, r.stdout)
    r = ph("checks")
    log = toy / "evals" / "workspace" / "run-phases" / "p" / "checks.log"
    case("checks with a failing command: exit 1, its FAIL line and detail, not its noise, the rest PASS",
         r.returncode == 1 and "FAIL python3 scripts/y.py (" in r.stdout and "    FAIL c\n        the detail" in r.stdout
         and "noise" not in r.stdout and "PASS check-contracts (" in r.stdout
         and "PASS python3 scripts/x.py (0s): 2/2 pass" in r.stdout and "checks: 2 of 3 pass" in r.stdout
         and "noise" in log.read_text(), r.stdout)
    case("finish after failed checks: exit 1", ph("finish", "--what", "greet").returncode == 1)
    (toy / "scripts" / "y.py").write_text("print('PASS b')\n")
    r = ph("checks")
    case("checks all passing: exit 0, one line per command, the site not built",
         r.returncode == 0 and "checks: 3 of 3 pass" in r.stdout and "build-site" not in r.stdout
         and not (toy / "site" / "docs").exists(), r.stdout)
    (toy / "skills" / "hello" / "SKILL.md").write_text("---\nname: hello\n---\nSay hello, by name.\n")
    r = ph("finish", "--what", "greet")
    case("finish after an edit made since checks passed: exit 1", r.returncode == 1 and "have not passed" in r.stdout, r.stdout)
    ph("checks")
    (notes / "p-01-greet.md").write_text("# 01 — greet\n\n## Deviations\n\nnone\n")
    (toy / "evals" / "2026-01-01-greet.md").write_text("# greet\n")
    with open(toy / "evals" / "README.md", "a") as f:
        f.write("| 2026-01-01 | greet | [2026-01-01-greet.md](2026-01-01-greet.md) |\n")
    r = ph("finish", "--what", "greet", "--log", "2026-01-01-greet.md")
    case("finish after checks, then the note and the eval log: committed; the log given by its bare name",
         r.returncode == 0 and "phase 1 committed" in r.stdout and "`2026-01-01-greet.md`" in (notes / "p-progress.md").read_text()
         and not sh("git", "status", "--porcelain", cwd=repo).stdout, r.stdout)
    (toy / "scripts" / "x.py").write_text("import time\ntime.sleep(30)\n")
    r = ph("checks", "--timeout", "1")
    case("checks with a command over --timeout: exit 1, said so",
         r.returncode == 1 and "FAIL python3 scripts/x.py" in r.stdout and "timed out after 1s" in r.stdout, r.stdout)
    # the items' cited lines carried from the reviewed commit to the tree as it stands
    base = sh("git", "rev-list", "--max-parents=0", "HEAD", cwd=repo).stdout.strip()[:10]
    (toy / "skills" / "hello" / "SKILL.md").write_text("# a\n# b\n---\nname: hello\n---\nSay hello, by name.\n")
    (notes / "p-edits.md").write_text(
        EDITS.replace("# toy p — edits\n", f"# toy p — edits\n\nReviewed today, against `{base}`.\n").replace(
            "- files: skills/hello/SKILL.md:5", "- files: skills/hello/SKILL.md:1-2, skills/hello/SKILL.md:4, "
            "`skills/wave/SKILL.md:4`, skills/gone/SKILL.md:1, README.md"))
    r = sh(sys.executable, EDITS_PY, "show", notes / "p-edits.md", "E-001", "--located", cwd=toy)
    case("show --located: a moved range, a changed line, an untouched one, a file that is gone; a bare path cites nothing",
         r.returncode == 0 and "skills/hello/SKILL.md:1-2 → :3-4, moved" in r.stdout
         and "skills/hello/SKILL.md:4 → :6, changed since the review" in r.stdout and "     6  Say hello, by name." in r.stdout
         and "skills/wave/SKILL.md:4 → :4, as reviewed" in r.stdout and "skills/gone/SKILL.md:1 → the file is gone" in r.stdout
         and "README.md →" not in r.stdout and f"as reviewed at `{base}`" in r.stdout, r.stdout)
    r = sh(sys.executable, EDITS_PY, "show", notes / "p-edits.md", "E-001", "--located", "--at", "HEAD", cwd=toy)
    case("show --located --at HEAD: carried from the commit given", "skills/hello/SKILL.md:4 → :6, moved" in r.stdout, r.stdout)
    r = sh(sys.executable, EDITS_PY, "show", notes / "p-edits.md", "E-001", cwd=toy)
    case("show without --located: the item only", r.returncode == 0 and "→" not in r.stdout, r.stdout)

    (notes / "p-00-overview.md").write_text(OVERVIEW.replace("**Init flags:**", "**Checks:** `no-such-program-xyz`\n\n**Init flags:**"))
    r = ph("checks")
    case("checks with a command that cannot start: exit 1, said so",
         r.returncode == 1 and "FAIL no-such-program-xyz" in r.stdout and "could not start" in r.stdout, r.stdout)


def main():
    tmp = Path(tempfile.mkdtemp(prefix="phases-check-"))
    repo = tmp / "repo"
    toy, notes = build(repo, OVERVIEW)
    git = GIT

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
         and "toy p (phase 1): <what>" in r.stdout and "## Its checks" not in r.stdout, r.stdout)
    case("brief: the overview's prose and pointers to its other sections, the phase marked as begun",
         "Names are exact." in r.stdout and "Breaking changes: `sed -n" in r.stdout
         and json.loads(mark.read_text())["phase"] == 1, r.stdout[-400:])

    case("brief against an edit list: this phase's item whole with the lines it cites, not another phase's",
         "## Its items, each with the lines it cites as they stand now" in r.stdout
         and "#### E-001 hello greets by name" in r.stdout and "E-002" not in r.stdout
         and "     4  Say hello." in r.stdout and "the list names no commit" in r.stdout, r.stdout)
    r = ph("brief", "--phase", "1", "--short")
    case("brief --short: without the edit list's part", r.returncode == 0 and "## Its items" not in r.stdout, r.stdout)

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
    r = ph("brief")
    script = PLUGIN_DEV / "skills" / "run-evals" / "scripts" / "eval_workspace.py"
    case("brief at a checkpoint: one exact init command per behavioral row, the plan's flags on each",
         f"- R3.e1: `python3 {script} init . hello --quiet --evals 1,3,4 --working-tree-only --reuse-unhashed`" in r.stdout
         and f"- R3.e2: `python3 {script} init . hello --quiet --evals 5 --reuse-unhashed`" in r.stdout
         and "This phase is one: its behavioral rows run here." in r.stdout, r.stdout)
    case("brief at the last phase: build-site is among its checks, as at no phase before",
         "checks p` runs `build-site` in one call" in r.stdout, r.stdout)
    r = ph("finish", "--what", "docs")
    case("finish at a checkpoint with a behavioral row not run: exit 1 naming the row",
         r.returncode == 1 and "row R3.e1 (hello) has no --iteration" in r.stdout, r.stdout)
    it = toy / "evals" / "workspace" / "hello" / "iteration-1"
    run = it / "eval-1-x" / "with_skill" / "run-1"
    run.mkdir(parents=True)

    def manifest(pairs):
        (it / "manifest.json").write_text(json.dumps({"target": "hello", "runs": [
            {"eval_id": i, "config": c} for i, c in pairs]}))

    manifest([(1, "with_skill"), (3, "with_skill"), (5, "with_skill")])
    (it / "report.md").write_text("# hello iteration-1\n")
    r = ph("finish", "--what", "docs", "--iteration", "evals/workspace/hello/iteration-1")
    case("finish: an eval id the row names and no iteration ran, exit 1 with the command",
         r.returncode == 1 and "row R3.e1: hello eval(s) [4] are in none of its iterations" in r.stdout
         and "--evals 1,3,4 --working-tree-only" in r.stdout, r.stdout)
    case("finish: a compared row run working tree only, exit 1",
         "row R3.e2: hello eval(s) [5] ran working tree only and the row runs them compared" in r.stdout, r.stdout)
    manifest([(i, c) for i in (1, 3, 4, 5) for c in ("with_skill", "old_skill")])
    (it / "report.md").unlink()
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

    r = ph("checks")
    case("checks at the end of a plan with a site and no **Checks:** line: the site built, nothing left in the tree",
         r.returncode == 0 and "PASS build-site (" in r.stdout and "checks: 1 of 1 pass" in r.stdout
         and (toy / "site" / "docs").is_dir() and not sh("git", "status", "--porcelain", cwd=repo).stdout, r.stdout)

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

    checks_cases(tmp)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{sum(results)}/{len(results)} pass")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
