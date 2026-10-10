#!/usr/bin/env python3
"""PreToolUse on Agent: an eval's runs are started by the runner, not one Agent call each.

Every executor or grader spawned through the Agent tool wakes the chat that spawned it when
it finishes, and each wake re-reads that chat's whole context: on one plan that cost as much
as every executor and grader together. `eval_workspace.py run` starts them from a script and
hands back one report.

Refuses (exit 2) a spawn whose prompt is an executor's or a grader's (the opening words of
`skills/run-evals/references/prompts.md`) for a run directory of an iteration whose
`manifest.json` does not say `"by_hand": true`. `init --by-hand` writes that for an eval
that only means something inside a subagent. Anything else exits 0 at once; a crash or an
unreadable event exits 0 with the reason on stderr.
"""
import json
import re
import sys
from pathlib import Path

SIGNS = ("You are testing `", "Do the following task as you would without any special instructions",
         "agents/grader.md` and follow it", "Grade one run of an eval")
RUN_DIR = re.compile(r"(/[^\s`'\"]*/evals/workspace/[\w.-]+/iteration-\d+)/eval-")


def main():
    event = json.load(sys.stdin)
    prompt = str((event.get("tool_input") or {}).get("prompt") or "")
    m = RUN_DIR.search(prompt)
    if not m or not any(s in prompt for s in SIGNS):
        return 0
    try:
        manifest = json.loads((Path(m.group(1)) / "manifest.json").read_text())
    except (OSError, ValueError):
        return 0        # not an iteration `init` laid out
    if manifest.get("by_hand"):
        return 0
    script = Path(__file__).resolve().parent.parent / "skills" / "run-evals" / "scripts" / "eval_workspace.py"
    print(f"plugin-dev: an eval's executors and graders are not spawned one Agent call each; "
          f"every completion would cost this chat a turn. Start them all with one background "
          f"command and read its report: python3 {script} run {m.group(1)} — for an eval that "
          f"must run inside a subagent, lay the iteration out again with `init --by-hand` "
          f"(run-evals, Without the runner).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    try:
        sys.exit(main())
    except Exception as e:      # a guard that crashes must not stop the session
        print(f"plugin-dev agent guard: {type(e).__name__}: {e}; allowing", file=sys.stderr)
        sys.exit(0)
