#!/usr/bin/env python3
"""Mechanical check of contract_sweep.py's `flow` claim and build_site.py's flow page, no model.

Builds a throwaway plugin whose `flow:` block agrees with its files, which must pass and
build; then plants one disagreement at a time, each of which the claim must fail on, naming
it: a skill a role's file starts naming, a use and a `names` entry the file no longer backs,
a document a new role names, a listed role that does not name its document, an agent that is
no role, a hook wired and not named, a hook named and not wired, a script that does not
exist, and a driver that is no skill.

Usage: python3 check.py        (exit 0 when every check passes)
"""

import json
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

SCRIPTS = Path(__file__).resolve().parents[3] / "scripts"
failed = 0

FILES = {
    ".claude-plugin/plugin.json": '{"name": "toy", "version": "0.1.0"}',
    "contracts.yml": "flow:\n  - name: flow\n    file: site/site.yml\n",
    "agents/worker.md": "---\nname: worker\ndescription: does: one step\nskills:\n  - lint\n---\n"
                        "Read `docs/plan.md`. Write `docs/out/<step>.md`. Invoke `fmt` when the step has code.\n",
    "skills/lint/SKILL.md": "---\nname: lint\ndescription: lint rules\n---\n# lint\n",
    "skills/fmt/SKILL.md": "---\nname: fmt\ndescription: format rules\n---\n# fmt\n",
    "skills/extra/SKILL.md": "---\nname: extra\ndescription: more rules\n---\n# extra\n",
    "skills/drive/SKILL.md": "---\nname: drive\ndescription: the driver\ndisable-model-invocation: true\n---\n"
                             "Run `p.py next`, spawn a worker, then `p.py finish`. The plan is `docs/plan.md`;\n"
                             "never run `lint` here.\n",
    "scripts/p.py": '"""next and finish."""\n',
    "hooks/gate.py": '"""the gate."""\n',
    "hooks/hooks.json": json.dumps({"hooks": {"SubagentStop": [{"hooks": [
        {"type": "command", "command": "python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/gate.py"]}]}]}}),
    "site/flow.md": "# The flow\n\n<!-- flow:agents-skills -->\n\n<!-- flow:writes -->\n\n<!-- flow:reads -->\n\n"
                    "<!-- flow:documents -->\n\n<!-- flow:drivers -->\n",
    "site/site.yml": """flow:
  roles: [drive, worker]
  uses:
    worker:
      sometimes:
        - fmt: the step has code
    drive:
      names: [lint]
  documents:
    - name: the plan
      path: docs/plan.md
      writes: [drive]
      reads: [worker]
    - name: step output
      path: docs/out/<step>.md
      writes: [worker]
      reads: [you]
  drivers:
    - skill: drive
      ledger: "`docs/progress.md`"
      next: "`p.py next`"
      spawns: one worker per step
      returns: "Status: done"
      writer: "`p.py finish`"
      held: "`gate.py` on `SubagentStop`"
""",
}


def plugin(root: Path) -> Path:
    if root.exists():
        shutil.rmtree(root)
    for rel, text in FILES.items():
        (root / rel).parent.mkdir(parents=True, exist_ok=True)
        (root / rel).write_text(text)
    return root


def sweep(root: Path) -> tuple[int, str]:
    r = subprocess.run([sys.executable, str(SCRIPTS / "contract_sweep.py"), str(root)],
                       capture_output=True, text=True)
    return r.returncode, r.stdout + r.stderr


def check(name: str, ok: bool, detail: str = "") -> None:
    global failed
    failed += not ok
    print(f"{'ok  ' if ok else 'FAIL'}  {name}" + (f"\n      {detail.strip()[:400]}" if not ok else ""))


def edit(root: Path, rel: str, old: str, new: str) -> None:
    text = (root / rel).read_text()
    assert old in text, (rel, old)
    (root / rel).write_text(text.replace(old, new, 1))


def defect(name: str, expect: str, change) -> None:
    """Plant one disagreement in a fresh copy; the sweep must exit 1 and say `expect`."""
    with tempfile.TemporaryDirectory() as tmp:
        root = plugin(Path(tmp) / "toy")
        change(root)
        code, out = sweep(root)
        check(name, code == 1 and expect in out, out)


with tempfile.TemporaryDirectory() as tmp:
    root = plugin(Path(tmp) / "toy")
    code, out = sweep(root)
    check("a block that agrees with its files passes", code == 0 and "2 roles, 2 documents" in out, out)
    r = subprocess.run([sys.executable, str(SCRIPTS / "build_site.py"), str(root)], capture_output=True, text=True)
    page = (root / "site/docs/flow.md").read_text() if r.returncode == 0 else ""
    check("the flow page builds with every part filled and no warning",
          r.returncode == 0 and "<!-- flow:" not in page and page.count("<svg") == 3
          and "●" in page and "○" in page and " ! " not in r.stdout, r.stdout + r.stderr)

defect("a skill a role's file starts naming is not placed", "agents/worker.md:7 names `extra`",
       lambda r: edit(r, "agents/worker.md", "Invoke `fmt`", "See `extra`. Invoke `fmt`"))
defect("a declared use the file no longer names", "flow.uses.worker lists `fmt`, which agents/worker.md never names",
       lambda r: edit(r, "agents/worker.md", " Invoke `fmt` when the step has code.", ""))
defect("a `names` entry the file no longer backs", "flow.uses.drive lists `lint`",
       lambda r: edit(r, "skills/drive/SKILL.md", "never run `lint` here.", "run nothing else here."))
defect("a use of a skill that does not exist", "`nope` is not a skill of this plugin",
       lambda r: edit(r, "site/site.yml", "- fmt: the step has code", "- fmt: the step has code\n        - nope: never"))
defect("a role that names a document it is not listed for", "names `step output`, and drive is not in its writes",
       lambda r: edit(r, "skills/drive/SKILL.md", "The plan is", "Its results are under `docs/out/<step>.md`. The plan is"))
defect("a listed role whose file never names the document", "`the plan` lists worker",
       lambda r: edit(r, "agents/worker.md", "Read `docs/plan.md`. ", ""))
defect("an agent that is not a role", "agents/helper.md is not in flow.roles",
       lambda r: (r / "agents/helper.md").write_text("---\nname: helper\ndescription: helps\n---\nHelp.\n"))
defect("a hook wired and named by no driver", "wires `late.py`, which no driver's `held` names",
       lambda r: ((r / "hooks/late.py").write_text('"""late."""\n'),
                  edit(r, "hooks/hooks.json", '"SubagentStop": [', '"Stop": [{"hooks": [{"type": "command", "command": '
                       '"python3", "args": ["${CLAUDE_PLUGIN_ROOT}/hooks/late.py"]}]}], "SubagentStop": [')))
defect("a hook named and not wired", "`gate.py` is not wired in hooks/hooks.json",
       lambda r: (r / "hooks/hooks.json").write_text('{"hooks": {}}'))
defect("a hook named on an event it is not wired to", "no hook named there is wired to `Stop`",
       lambda r: edit(r, "site/site.yml", "`gate.py` on `SubagentStop`", "`gate.py` on `Stop`"))
defect("a script that does not exist", "`q.py` is not a script or hook of this plugin",
       lambda r: edit(r, "site/site.yml", "`p.py next`", "`q.py next`"))
defect("a script the driver's file never names", "skills/drive/SKILL.md never names `p.py`",
       lambda r: edit(r, "skills/drive/SKILL.md", "Run `p.py next`, spawn a worker, then `p.py finish`.", "Spawn a worker."))
defect("a driver that is not a skill", "`steer` is not a skill of this plugin",
       lambda r: edit(r, "site/site.yml", "- skill: drive", "- skill: steer"))
defect("no flow block at all", "has no `flow:` block",
       lambda r: (r / "site/site.yml").write_text("workflows_order: []\n"))

print(f"\n{'all passed' if not failed else f'{failed} failed'}")
sys.exit(1 if failed else 0)
