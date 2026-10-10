#!/usr/bin/env python3
"""Mechanical check of `eval_workspace.py` init/run/report, with no model.

    python3 evals/fixtures/run-evals-runner/check.py

Builds a throwaway git repo holding a one-skill plugin with a committed baseline and an
edited working tree, points RUN_EVALS_CLAUDE at fake_claude.py, and walks the cases below.
Prints PASS or FAIL per case and `<n>/<m> pass`; exits 1 on any FAIL.
"""
import json
import os
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

HERE = Path(__file__).resolve().parent
SCRIPT = HERE.parents[2] / "skills" / "run-evals" / "scripts" / "eval_workspace.py"
results = []


def case(name, ok, detail=""):
    results.append(ok)
    print(f"{'PASS' if ok else 'FAIL'} {name}{'' if ok else ' — ' + str(detail)}")


def sh(*args, cwd, env=None):
    return subprocess.run([str(a) for a in args], cwd=cwd, env=env, capture_output=True, text=True)


def write_set(plugin, evals):
    (plugin / "evals" / "sets" / "hello.json").write_text(json.dumps(
        {"target": "hello", "target_path": "skills/hello/SKILL.md", "evals": evals}, indent=2))


def an_eval(eid, name, expectations, prompt=None):
    return {"id": eid, "name": name, "kind": "behavioral", "baseline": "previous",
            "harness": "evals/sets/files/hello/answers.md",
            "prompt": prompt or f"/toy:hello {name}", "expected_output": "a greeting",
            "files": [], "expectations": expectations, "added_in": "check"}


def main():
    tmp = Path(tempfile.mkdtemp(prefix="run-evals-check-"))
    repo, state = tmp / "repo", tmp / "state"
    plugin = repo / "toy"
    (plugin / ".claude-plugin").mkdir(parents=True)
    (plugin / "skills" / "hello").mkdir(parents=True)
    (plugin / "evals" / "sets" / "files" / "hello").mkdir(parents=True)
    state.mkdir()
    (plugin / ".claude-plugin" / "plugin.json").write_text('{"name": "toy", "version": "0.1.0"}\n')
    (plugin / "skills" / "hello" / "SKILL.md").write_text("---\nname: hello\n---\nSay hello.\n")
    (plugin / "evals" / "sets" / "files" / "hello" / "answers.md").write_text("- yes\n")
    base_evals = [an_eval(1, "plain", ["greets the user", "names the repo [fail:old_skill]"]),
                  an_eval(2, "loud", ["greets the user", "is polite [fail:with_skill]"])]
    write_set(plugin, base_evals)
    sh("git", "init", "-q", "-b", "main", cwd=repo)
    sh("git", "add", "-A", cwd=repo)
    sh("git", "-c", "user.name=t", "-c", "user.email=t@t", "commit", "-qm", "base", cwd=repo)
    sh("git", "checkout", "-qb", "work", cwd=repo)
    (plugin / "skills" / "hello" / "SKILL.md").write_text("---\nname: hello\n---\nSay hello, and name the repo.\n")

    (tmp / "scratch").mkdir()       # the runner's per-run scratch directories land here
    env = dict(os.environ, RUN_EVALS_CLAUDE=str(HERE / "fake_claude.py"), FAKE_STATE=str(state),
               CLAUDECODE="1", TMPDIR=str(tmp / "scratch"))

    def init(*flags):
        r = sh(sys.executable, SCRIPT, "init", plugin, "hello", *flags, cwd=plugin, env=env)
        return (json.loads(r.stdout) if r.returncode == 0 else None), r

    def run(it, plan=None, *flags):
        (state / "calls.jsonl").unlink(missing_ok=True)
        e = dict(env, FAKE_PLAN=json.dumps(plan or {}))
        r = sh(sys.executable, SCRIPT, "run", it, "--jobs", "4", *flags, cwd=plugin, env=e)
        calls = [json.loads(x) for x in (state / "calls.jsonl").read_text().splitlines()] \
            if (state / "calls.jsonl").exists() else []
        return r, calls

    def count(calls, role):
        return sum(1 for c in calls if c["role"] == role)

    # 1 — a first iteration runs both sides and grades every run
    m1, r = init()
    it1 = Path(m1["iteration"])
    case("init: 4 runs, each with an inputs_hash, model recorded, snapshot made",
         len(m1["runs"]) == 4 and all(x.get("inputs_hash") for x in m1["runs"])
         and m1["model"] == "claude-sonnet-5-5" and (it1 / "baseline-snapshot").is_dir(), m1)
    r, calls = run(it1, None, "--dry-run")
    case("run --dry-run: lists 4 executors and 4 graders, starts nothing",
         r.returncode == 0 and r.stdout.count("execute ") == 4 and r.stdout.count("grade ") == 4
         and not calls, r.stdout + r.stderr)
    r, calls = run(it1)
    case("run: 4 executor and 4 grader sessions, exit 0",
         r.returncode == 0 and count(calls, "executor") == 4 and count(calls, "grader") == 4,
         r.stdout + r.stderr)
    case("run: every grader starts after the last executor",
         [c["role"] for c in calls] == ["executor"] * 4 + ["grader"] * 4, calls)
    case("run: sessions run in the plugin directory, on the manifest's model, un-nested, scratch made",
         all(Path(c["cwd"]).resolve() == plugin.resolve() and c["model"] == "claude-sonnet-5-5"
             and not c["nested_flag_seen"] and c["add_dirs_exist"] for c in calls), calls)
    old_said = (it1 / "eval-1-plain" / "old_skill" / "run-1" / "outputs" / "said.txt").read_text()
    new_said = (it1 / "eval-1-plain" / "with_skill" / "run-1" / "outputs" / "said.txt").read_text()
    case("run: the baseline executor read the snapshot's target, the other the working tree's",
         "name the repo" in new_said and "name the repo" not in old_said, (old_said, new_said))
    timing = json.loads((it1 / "eval-1-plain" / "with_skill" / "run-1" / "timing.json").read_text())
    grading = json.loads((it1 / "eval-1-plain" / "with_skill" / "run-1" / "grading.json").read_text())
    case("run: timing.json sums the session's usage; the grader's timing copy is dropped",
         timing["total_tokens"] == 4330 and timing["attempts"] == 1 and "timing" not in grading, timing)
    case("report: pass rates per side, the working tree's failure with the baseline's verdict",
         "**Pass rate:** 3/4 (75.0%) vs 3/4 (75.0%)" in r.stdout
         and "eval 2, expectation 2 (baseline: passed)" in r.stdout
         and "eval 1: names the repo" in r.stdout and (it1 / "report.md").is_file(), r.stdout)

    # 2 — the next iteration reuses both baselines
    q, r = init("--quiet")
    case("init --quiet: the path, the counts and the warnings; no prompt, no expectation",
         q["executors_to_run"] == 2 and q["baseline_runs_reused"] == 2 and q["warnings"] == []
         and "greets the user" not in r.stdout and "runs" not in q, r.stdout)
    shutil.rmtree(q["iteration"])
    m2, r = init()
    it2 = Path(m2["iteration"])
    reused = [x for x in m2["runs"] if x["reused_from"]]
    case("init again: both baseline runs reused, no snapshot, nothing to regrade",
         len(reused) == 2 and all(x["config"] == "old_skill" for x in reused)
         and not (it2 / "baseline-snapshot").exists()
         and all((Path(x["run_dir"]) / "grading.json").is_file() for x in reused), m2)
    r, calls = run(it2)
    case("run: 2 executors and 2 graders; the report still has the baseline column",
         count(calls, "executor") == 2 and count(calls, "grader") == 2
         and "vs 3/4 (75.0%)" in r.stdout and "2 baseline run(s) reused" in r.stdout, r.stdout)

    # 3 — a changed expectation regrades the reused baseline and reruns nothing
    write_set(plugin, [an_eval(1, "plain", ["greets the user", "names the repo [fail:old_skill]", "is short"]),
                       base_evals[1]])
    m3, r = init()
    r, calls = run(m3["iteration"])
    case("changed expectations: baseline outputs reused and graded again (2 executors, 3 graders)",
         count(calls, "executor") == 2 and count(calls, "grader") == 3
         and "**Pass rate:** 4/5" in r.stdout, r.stdout)

    # 4 — a changed prompt or harness is a different run
    write_set(plugin, [an_eval(1, "plain", ["greets the user"], prompt="/toy:hello plainly"), base_evals[1]])
    m4, r = init()
    case("changed prompt: that eval's baseline runs again, the other is reused",
         sorted((x["eval_id"], bool(x["reused_from"])) for x in m4["runs"] if x["config"] == "old_skill")
         == [(1, False), (2, True)], m4)
    shutil.rmtree(m4["iteration"])
    (plugin / "evals" / "sets" / "files" / "hello" / "answers.md").write_text("- no\n")
    m4, r = init()
    case("changed harness sheet: no baseline is reused",
         not any(x["reused_from"] for x in m4["runs"]), m4)
    shutil.rmtree(m4["iteration"])
    (plugin / "evals" / "sets" / "files" / "hello" / "answers.md").write_text("- yes\n")
    write_set(plugin, base_evals)

    # 5 — another model, --no-reuse, and manifests written before inputs_hash
    m5, r = init("--model", "claude-opus-5-5")
    case("--model: recorded, and a baseline run on another model is not reused",
         m5["model"] == "claude-opus-5-5" and not any(x["reused_from"] for x in m5["runs"]), m5)
    shutil.rmtree(m5["iteration"])
    m5, r = init("--no-reuse")
    case("--no-reuse: every baseline runs again", not any(x["reused_from"] for x in m5["runs"]), m5)
    shutil.rmtree(m5["iteration"])
    for it in (it1, it2, Path(m3["iteration"])):
        man = json.loads((it / "manifest.json").read_text())
        for x in man["runs"]:
            x.pop("inputs_hash", None)
        man.pop("model", None)
        (it / "manifest.json").write_text(json.dumps(man))
    m5, r = init()
    case("a manifest with no inputs_hash is not reused by default",
         not any(x["reused_from"] for x in m5["runs"]), m5)
    shutil.rmtree(m5["iteration"])
    m5, r = init("--reuse-unhashed")
    case("--reuse-unhashed: it is, on prompt and harness name",
         sum(1 for x in m5["runs"] if x["reused_from"]) == 2, m5)
    shutil.rmtree(m5["iteration"])

    # 6 — working tree only: evals 1 and 2 have a baseline to reuse again, eval 3 never ran
    m, r = init()
    run(m["iteration"])
    write_set(plugin, base_evals + [an_eval(3, "new", ["greets the user"])])
    m6, r = init("--working-tree-only")
    configs = sorted((x["eval_id"], x["config"]) for x in m6["runs"])
    case("--working-tree-only: no baseline for the eval never run, a warning naming it",
         (3, "old_skill") not in configs and (3, "with_skill") in configs
         and (1, "old_skill") in configs and not (Path(m6["iteration"]) / "baseline-snapshot").exists()
         and any("[3]" in w for w in m6["warnings"]) and "warning:" in r.stderr, (configs, m6["warnings"]))
    r, calls = run(m6["iteration"])
    case("--working-tree-only: only working-tree executors run; the new eval's baseline cell is empty",
         all("with_skill" in c["run_dir"] for c in calls if c["role"] == "executor")
         and "| 3 `new` | 1/1 | — |" in r.stdout and "working tree only" in r.stdout, r.stdout)
    write_set(plugin, base_evals)

    # 7 — thrown-away attempts
    m7, r = init("--no-reuse")
    it7 = Path(m7["iteration"])
    r, calls = run(it7, {"error_once": ["eval-1-plain/with_skill"],
                         "peek_once": ["eval-2-loud/with_skill"],
                         "always_error": ["eval-2-loud/old_skill"]})
    t = json.loads((it7 / "eval-1-plain" / "with_skill" / "run-1" / "timing.json").read_text())
    case("an executor that errors once is run again and counted (attempts 2)", t["attempts"] == 2, t)
    t = json.loads((it7 / "eval-2-loud" / "with_skill" / "run-1" / "timing.json").read_text())
    log = (it7 / "run.log").read_text()
    case("an executor that names manifest.json is thrown away and run again",
         t["attempts"] == 2 and "void: a tool call named" in log, log)
    dead = it7 / "eval-2-loud" / "old_skill" / "run-1"
    case("two errors: not-run.json, no grader for it, exit 1, the report says so",
         (dead / "not-run.json").is_file() and not (dead / "grading.json").exists()
         and r.returncode == 1 and "not run:" in r.stdout
         and not any(c["role"] == "grader" and "eval-2-loud/old_skill" in c["run_dir"] for c in calls),
         r.stdout)
    m8, r = init()
    case("a run that was not run is never reused; an older finished one is",
         all(x["reused_from"] and (x["eval_id"] != 2 or str(it7) not in x["reused_from"])
             for x in m8["runs"] if x["config"] == "old_skill"),
         [(x["eval_id"], x["reused_from"]) for x in m8["runs"] if x["config"] == "old_skill"])

    # 8 — rerunning `run` picks up only what is owed
    r, calls = run(it7)
    case("run again retries only the run that was not run, grades it, exit 0",
         count(calls, "executor") == 1 and count(calls, "grader") == 1 and r.returncode == 0
         and all("eval-2-loud/old_skill" in c["run_dir"] for c in calls)
         and not (dead / "not-run.json").exists(), calls)
    r, calls = run(it7)
    case("run on a finished iteration starts nothing and prints the report",
         not calls and r.returncode == 0 and "**Pass rate:**" in r.stdout, calls)

    only_git = tmp / "bin"
    only_git.mkdir()
    (only_git / "git").symlink_to(shutil.which("git"))
    r = sh(sys.executable, SCRIPT, "run", it1, cwd=plugin,
           env=dict(env, RUN_EVALS_CLAUDE="", PATH=str(only_git)))
    case("no claude binary: exit 2 and a pointer to the fallback",
         r.returncode == 2 and "Without the runner" in r.stderr, r.stderr)

    shutil.rmtree(tmp, ignore_errors=True)
    print(f"{sum(results)}/{len(results)} pass")
    return 0 if all(results) else 1


if __name__ == "__main__":
    sys.exit(main())
