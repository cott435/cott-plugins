#!/usr/bin/env python3
"""A stand-in for `claude -p`, for check.py: no model, the same output shape.

It reads the prompt `eval_workspace.py run` passes, does what a session given that prompt
would leave behind (an executor writes transcript.md and an output; a grader writes
grading.json), and prints a stream-json result record. FAKE_PLAN (JSON) makes chosen runs
misbehave, each key a list of substrings of the run directory:

    error_once     the first attempt exits 1 with no result record
    always_error   every attempt does
    peek_once      the first attempt's tool call names the iteration's manifest.json

A grader fails any expectation whose text holds `[fail:<config>]` for its run's
configuration. Every call appends one JSON line to $FAKE_STATE/calls.jsonl.
"""
import json
import os
import re
import sys
from pathlib import Path

argv = sys.argv[1:]
prompt = argv[argv.index("-p") + 1]
model = argv[argv.index("--model") + 1]
add_dirs = [argv[i + 1] for i, a in enumerate(argv) if a == "--add-dir"]
state = Path(os.environ["FAKE_STATE"])
plan = json.loads(os.environ.get("FAKE_PLAN") or "{}")


def emit(obj):
    print(json.dumps(obj), flush=True)


def planned(key, run_dir):
    return any(s in run_dir for s in plan.get(key, []))


def attempt_number(run_dir, role):
    counter = state / (re.sub(r"\W+", "_", run_dir) + f".{role}")
    n = int(counter.read_text()) + 1 if counter.exists() else 1
    counter.write_text(str(n))
    return n


def result():
    emit({"type": "result", "subtype": "success", "is_error": False, "result": "done",
          "num_turns": 3, "total_cost_usd": 0.01,
          "usage": {"input_tokens": 10, "output_tokens": 20,
                    "cache_creation_input_tokens": 300, "cache_read_input_tokens": 4000}})


grader = re.search(r"Write\s+`([^`]+)/grading\.json`", prompt)
role = "grader" if grader else "executor"
run_dir = grader.group(1) if grader else re.search(r"Keep `([^`]+)/transcript\.md`", prompt).group(1)
n = attempt_number(run_dir, role)
with open(state / "calls.jsonl", "a") as f:
    f.write(json.dumps({"role": role, "run_dir": run_dir, "attempt": n, "model": model,
                        "add_dirs_exist": all(os.path.isdir(d) for d in add_dirs),
                        "nested_flag_seen": "CLAUDECODE" in os.environ,
                        "cwd": os.getcwd()}) + "\n")
emit({"type": "system", "subtype": "init", "model": model})

if role == "executor":
    if planned("always_error", run_dir) or (planned("error_once", run_dir) and n == 1):
        print("API Error: overloaded", file=sys.stderr)
        sys.exit(1)
    target = re.search(r"Read tool on\s+`([^`]+)`", prompt)
    reads = target.group(1) if target else "nothing"
    if planned("peek_once", run_dir) and n == 1:
        reads = str(Path(run_dir).parents[2] / "manifest.json")
    emit({"type": "assistant", "message": {"content": [
        {"type": "tool_use", "name": "Read", "input": {"file_path": reads}}]}})
    said = Path(reads).read_text() if target and Path(reads).is_file() else "no target"
    Path(run_dir, "outputs").mkdir(parents=True, exist_ok=True)
    Path(run_dir, "outputs", "said.txt").write_text(said)
    Path(run_dir, "transcript.md").write_text(f"1. Read {reads}\n2. Wrote outputs/said.txt\n")
    result()
else:
    config = Path(run_dir).parent.name
    listed = re.search(r"expectations: (\[.*?\])\.?\s+transcript_path", prompt, re.S)
    graded = [{"text": t, "passed": f"[fail:{config}]" not in t, "evidence": f"said.txt, {config}"}
              for t in json.loads(listed.group(1))]
    passed = sum(1 for g in graded if g["passed"])
    Path(run_dir, "grading.json").write_text(json.dumps({
        "expectations": graded,
        "summary": {"passed": passed, "failed": len(graded) - passed, "total": len(graded),
                    "pass_rate": passed / len(graded)},
        "timing": {"total_duration_seconds": 1.0},
        "eval_feedback": {"suggestions": [{"assertion": graded[0]["text"],
                                           "reason": "would pass for any output"}]}}))
    result()
