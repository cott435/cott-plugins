#!/usr/bin/env python3
"""The workspace and set helper for run-evals.

    eval_workspace.py validate <set.json | set.trigger.json>...
    eval_workspace.py init <plugin-dir> <target> [--evals 1,2,3] [--baseline REF]
    eval_workspace.py timing <run-dir> --tokens N --duration-ms N
    eval_workspace.py finalize <iteration-dir>
    eval_workspace.py review <iteration-dir> [generate_review.py args...]
    eval_workspace.py locate-skill-creator

`init` lays out evals/workspace/<target>/iteration-N/ the way skill-creator's
aggregate_benchmark.py and eval-viewer/generate_review.py expect it, and prints a JSON
manifest of the runs to spawn. Stdlib only.
"""

import argparse
import glob
import json
import os
import subprocess
import sys
from pathlib import Path

KINDS = ("mechanical", "load", "behavioral", "trigger", "platform-fact")
REQUIRED_TOP = ("target", "target_path", "evals")
REQUIRED_EVAL = ("id", "name", "kind", "baseline", "prompt", "expected_output",
                 "files", "expectations", "added_in")

# Search order for skill-creator, established by 0.9-evals E0.1. The first directory
# holding both agents/grader.md and scripts/aggregate_benchmark.py wins.
SKILL_CREATOR_GLOBS = (
    "$SKILL_CREATOR_DIR",
    "~/.claude/plugins/cache/*/skill-creator/*/skills/skill-creator",
    "~/.claude/plugins/marketplaces/*/plugins/skill-creator/skills/skill-creator",
    "~/.claude/skills/skill-creator",
    "~/Library/Application Support/Claude/**/skills/skill-creator",
)


def git(cwd, *args):
    return subprocess.run(["git", *args], cwd=cwd, capture_output=True, text=True)


def plugin_root(start):
    """The nearest directory at or above `start` holding .claude-plugin/plugin.json."""
    p = Path(start).resolve()
    for d in [p, *p.parents]:
        if (d / ".claude-plugin" / "plugin.json").is_file():
            return d
    return None


# ---------------------------------------------------------------- validate

def validate_set(path, require_target=False):
    # A set is written in a plan's phase 0, before the phase that creates its target, so
    # `validate` accepts a missing target_path; `init` cannot run without one and requires it.
    problems = []
    path = Path(path)
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path}: cannot read: {e}"]
    if not isinstance(data, dict):
        return [f"{path}: top level must be an object"]
    for key in REQUIRED_TOP:
        if key not in data:
            problems.append(f"{path}: missing top-level key '{key}'")
    root = plugin_root(path.parent) or path.parent
    if require_target and "target_path" in data and not (root / data["target_path"]).exists():
        problems.append(f"{path}: target_path '{data['target_path']}' does not exist")
    evals = data.get("evals", [])
    if not isinstance(evals, list) or not evals:
        problems.append(f"{path}: 'evals' must be a non-empty list")
        return problems
    seen = set()
    for i, ev in enumerate(evals):
        eid = ev.get("id", f"#{i + 1}")
        where = f"{path}: eval {eid}"
        for key in REQUIRED_EVAL:
            if key not in ev:
                problems.append(f"{where}: missing '{key}'")
        if "id" in ev:
            if not isinstance(ev["id"], int) or isinstance(ev["id"], bool):
                problems.append(f"{where}: id must be an integer")
            elif ev["id"] in seen:
                problems.append(f"{where}: duplicate id")
            seen.add(ev["id"])
        if "kind" in ev and ev["kind"] not in KINDS:
            problems.append(f"{where}: kind '{ev['kind']}' is not one of {', '.join(KINDS)}")
        base = ev.get("baseline")
        if base is not None and base not in ("none", "previous"):
            r = git(root, "rev-parse", "--verify", "--quiet", f"{base}^{{commit}}")
            if r.returncode != 0:
                problems.append(f"{where}: baseline '{base}' is not none, previous, or a git ref")
        if ev.get("harness") and not (root / ev["harness"]).is_file():
            problems.append(f"{where}: harness '{ev['harness']}' does not exist")
        if "files" in ev and not isinstance(ev["files"], list):
            problems.append(f"{where}: files must be a list")
        exp = ev.get("expectations")
        if exp is not None and not isinstance(exp, list):
            problems.append(f"{where}: expectations must be a list")
        elif ev.get("kind") == "behavioral" and not exp:
            problems.append(f"{where}: behavioral eval has no expectations")
        runs = ev.get("runs", 1)
        if not isinstance(runs, int) or runs < 1:
            problems.append(f"{where}: runs must be a positive integer")
    return problems


def mentions_outside(query):
    """A should-not query placed outside a plugin repo: it does not say `plugin`, or it
    says it is not one. The guard in SKILL.md, Trigger evals, keeps these from triggering."""
    q = query.lower()
    return "plugin" not in q or "not a plugin" in q


def validate_trigger_set(path):
    """skill-creator's run_eval format: a list of {query, should_trigger}."""
    path = Path(path)
    try:
        data = json.loads(path.read_text())
    except (OSError, json.JSONDecodeError) as e:
        return [f"{path}: cannot read: {e}"]
    if not isinstance(data, list) or not data:
        return [f"{path}: top level must be a non-empty list of {{query, should_trigger}}"]
    problems, counts, outside, seen = [], {True: 0, False: 0}, 0, set()
    for i, item in enumerate(data, 1):
        where = f"{path}: query {i}"
        if not isinstance(item, dict):
            problems.append(f"{where}: must be an object")
            continue
        q, st = item.get("query"), item.get("should_trigger")
        if not isinstance(q, str) or not q.strip():
            problems.append(f"{where}: 'query' must be a non-empty string")
        elif q in seen:
            problems.append(f"{where}: duplicate query")
        else:
            seen.add(q)
        if not isinstance(st, bool):
            problems.append(f"{where}: 'should_trigger' must be true or false")
            continue
        counts[st] += 1
        if st is False and isinstance(q, str) and mentions_outside(q):
            outside += 1
    for value, label in ((True, "should-trigger"), (False, "should-not-trigger")):
        if counts[value] < 8:
            problems.append(f"{path}: {counts[value]} {label} queries; at least 8 needed")
    if outside < 3:
        problems.append(f"{path}: {outside} should-not queries outside a plugin repo; at least 3 needed")
    return problems


def cmd_validate(args):
    problems = []
    for p in args.sets:
        problems += validate_trigger_set(p) if str(p).endswith(".trigger.json") else validate_set(p)
    for line in problems:
        print(line)
    return 1 if problems else 0


# ---------------------------------------------------------------- init

def default_branch(root):
    r = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    for name in ("main", "master"):
        if git(root, "rev-parse", "--verify", "--quiet", name).returncode == 0:
            return name
    return None


def resolve_previous(root):
    """The commit the current work started from: the merge-base with the default branch
    when HEAD is on another branch, else HEAD itself (the parent of uncommitted work)."""
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    branch = default_branch(root)
    if branch:
        mb = git(root, "merge-base", "HEAD", branch).stdout.strip()
        if mb and mb != head:
            return mb
    return head


def snapshot(root, ref, target_dir, dest):
    """git archive <ref> <target_dir> into dest, keeping repo-relative paths."""
    top = Path(git(root, "rev-parse", "--show-toplevel").stdout.strip())
    rel = (root / target_dir).resolve().relative_to(top)
    dest.mkdir(parents=True, exist_ok=True)
    arch = subprocess.run(["git", "archive", "--format=tar", ref, "--", str(rel)],
                          cwd=top, capture_output=True)
    if arch.returncode != 0:
        raise SystemExit(f"git archive {ref} {rel} failed: {arch.stderr.decode().strip()}"
                         " — if the target is new, its baseline is 'none'")
    tar = subprocess.run(["tar", "-x", "-C", str(dest)], input=arch.stdout, capture_output=True)
    if tar.returncode != 0:
        raise SystemExit(f"tar -x failed: {tar.stderr.decode().strip()}")
    return dest / rel


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def cmd_init(args):
    root = Path(args.plugin_dir).resolve()
    set_path = root / "evals" / "sets" / f"{args.target}.json"
    if not set_path.is_file():
        print(f"no set at {set_path}")
        return 1
    problems = validate_set(set_path, require_target=True)
    if problems:
        print("\n".join(problems))
        return 1
    data = json.loads(set_path.read_text())
    evals = [e for e in data["evals"] if e["kind"] == "behavioral"]
    if args.evals:
        wanted = {int(x) for x in args.evals.split(",")}
        missing = wanted - {e["id"] for e in data["evals"]}
        if missing:
            print(f"eval id(s) not in the set: {sorted(missing)}")
            return 1
        evals = [e for e in evals if e["id"] in wanted]
    if not evals:
        print("no behavioral evals selected")
        return 1

    bases = {args.baseline or e["baseline"] for e in evals}
    if len(bases) > 1:
        print(f"selected evals have different baselines {sorted(bases)}: "
              "run them as separate iterations or pass --baseline")
        return 1
    base = bases.pop()

    tdir = root / "evals" / "workspace" / args.target
    n = 1
    while (tdir / f"iteration-{n}").exists():
        n += 1
    it = tdir / f"iteration-{n}"
    it.mkdir(parents=True)

    target_file = root / data["target_path"]
    if base == "none":
        base_config, base_file, ref = "without_skill", None, None
    else:
        ref = resolve_previous(root) if base == "previous" else base
        ref = git(root, "rev-parse", "--short", f"{ref}^{{commit}}").stdout.strip()
        snap = snapshot(root, ref, Path(data["target_path"]).parent, it / "baseline-snapshot")
        base_file = snap / Path(data["target_path"]).name
        base_config = "old_skill"

    runs = []
    for ev in evals:
        edir = it / f"eval-{ev['id']}-{ev['name']}"
        meta = {"eval_id": ev["id"], "eval_name": ev["name"], "prompt": ev["prompt"],
                "assertions": ev["expectations"]}
        write_json(edir / "eval_metadata.json", meta)
        harness = str(root / ev["harness"]) if ev.get("harness") else None
        for config, tfile in (("with_skill", target_file), (base_config, base_file)):
            write_json(edir / config / "eval_metadata.json", meta)
            for k in range(1, ev.get("runs", 1) + 1):
                rdir = edir / config / f"run-{k}"
                (rdir / "outputs").mkdir(parents=True)
                runs.append({
                    "eval_id": ev["id"], "name": ev["name"], "config": config,
                    "run_dir": str(rdir), "outputs_dir": str(rdir / "outputs"),
                    "prompt": ev["prompt"], "harness": harness,
                    "target_file": str(tfile) if tfile else None,
                    "expectations": ev["expectations"],
                })

    manifest = {"iteration": str(it), "baseline_ref": ref,
                "skill_creator": locate_skill_creator(), "runs": runs}
    write_json(it / "manifest.json", manifest)
    print(json.dumps(manifest, indent=2))
    return 0


# ---------------------------------------------------------------- timing

def cmd_timing(args):
    write_json(Path(args.run_dir) / "timing.json", {
        "total_tokens": args.tokens,
        "duration_ms": args.duration_ms,
        "total_duration_seconds": round(args.duration_ms / 1000, 1),
    })
    return 0


# ---------------------------------------------------------------- finalize

def cmd_finalize(args):
    """Before aggregate_benchmark: drop the `timing` block a grader copies into grading.json.

    aggregate_benchmark reads tokens from timing.json only when grading.json has no timing;
    with the grader's copy present it falls back to execution_metrics.output_chars, or 0.
    timing.json, written from the completion notice, is the source of truth.
    """
    it = Path(args.iteration)
    fixed, missing = 0, []
    for rdir in sorted(it.glob("eval-*/*/run-*")):
        grading, timing = rdir / "grading.json", rdir / "timing.json"
        if not grading.is_file():
            missing.append(f"{rdir}: no grading.json")
            continue
        if not timing.is_file():
            missing.append(f"{rdir}: no timing.json")
            continue
        g = json.loads(grading.read_text())
        if "timing" in g:
            del g["timing"]
            write_json(grading, g)
            fixed += 1
    for line in missing:
        print(line)
    print(f"{fixed} grading.json file(s) now defer to timing.json")
    return 1 if missing else 0


# ---------------------------------------------------------------- review

class _ScriptSafeJson:
    """json for generate_review.py with `</` escaped as `<\\/`.

    The viewer inlines every output file into a <script> block with json.dumps, which does
    not escape `</script>`; an HTML output (a proposal page) ends the viewer's script early
    and the page renders empty. `<\\/` is the same string to JSON and inert to HTML.
    """
    def __getattr__(self, name):
        return getattr(json, name)

    @staticmethod
    def dumps(obj, *a, **kw):
        return json.dumps(obj, *a, **kw).replace("</", "<\\/")


def cmd_review(args):
    import importlib.util
    sc = locate_skill_creator()
    if not sc:
        print("skill-creator not found — no viewer; see SKILL.md, When skill-creator is missing")
        return 1
    path = Path(sc) / "eval-viewer" / "generate_review.py"
    spec = importlib.util.spec_from_file_location("generate_review", path)
    mod = importlib.util.module_from_spec(spec)
    spec.loader.exec_module(mod)
    mod.json = _ScriptSafeJson()
    sys.argv = [str(path), args.iteration, *args.rest]
    mod.main()
    return 0


# ---------------------------------------------------------------- locate

def locate_skill_creator():
    for pattern in SKILL_CREATOR_GLOBS:
        if pattern.startswith("$"):
            candidates = [os.environ[pattern[1:]]] if os.environ.get(pattern[1:]) else []
        else:
            candidates = sorted(glob.glob(os.path.expanduser(pattern), recursive=True),
                                key=lambda p: os.path.getmtime(p), reverse=True)
        for c in candidates:
            d = Path(c)
            if (d / "agents" / "grader.md").is_file() and \
               (d / "scripts" / "aggregate_benchmark.py").is_file():
                return str(d)
    return None


def cmd_locate(args):
    found = locate_skill_creator()
    if found:
        print(found)
        return 0
    print("skill-creator not found")
    return 1


def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    v = sub.add_parser("validate")
    v.add_argument("sets", nargs="+")
    v.set_defaults(fn=cmd_validate)
    i = sub.add_parser("init")
    i.add_argument("plugin_dir")
    i.add_argument("target")
    i.add_argument("--evals")
    i.add_argument("--baseline")
    i.set_defaults(fn=cmd_init)
    t = sub.add_parser("timing")
    t.add_argument("run_dir")
    t.add_argument("--tokens", type=int, required=True)
    t.add_argument("--duration-ms", type=int, required=True)
    t.set_defaults(fn=cmd_timing)
    f = sub.add_parser("finalize")
    f.add_argument("iteration")
    f.set_defaults(fn=cmd_finalize)
    r = sub.add_parser("review")
    r.add_argument("iteration")
    r.add_argument("rest", nargs=argparse.REMAINDER)
    r.set_defaults(fn=cmd_review)
    loc = sub.add_parser("locate-skill-creator")
    loc.set_defaults(fn=cmd_locate)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
