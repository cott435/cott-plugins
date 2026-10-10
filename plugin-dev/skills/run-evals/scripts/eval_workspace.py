#!/usr/bin/env python3
"""The workspace and set helper for run-evals.

    eval_workspace.py validate <set.json | set.trigger.json>...
    eval_workspace.py init <plugin-dir> <target> [--evals 1,2,3] [--baseline REF]
                           [--working-tree-only] [--no-reuse] [--reuse-unhashed] [--model ID] [-q]
                           [--by-hand]
    eval_workspace.py run <iteration-dir> [--jobs N] [--timeout SECONDS] [--dry-run]
    eval_workspace.py report <iteration-dir>
    eval_workspace.py timing <run-dir> --tokens N --duration-ms N
    eval_workspace.py finalize <iteration-dir>
    eval_workspace.py review <iteration-dir> [generate_review.py args...]
    eval_workspace.py blind <iteration-dir>
    eval_workspace.py locate-skill-creator

`init` lays out evals/workspace/<target>/iteration-N/ the way skill-creator's
aggregate_benchmark.py and eval-viewer/generate_review.py expect it, and prints a JSON
manifest of the runs to spawn. A baseline run an earlier iteration already finished at the
same ref, with the same inputs and model, is copied in and not run again. `run` executes
and grades every run the manifest still owes as headless `claude -p` sessions and prints
one report, so the chat that called it reads a table and not seventy completion notices.
Stdlib only.
"""

import argparse
import concurrent.futures
import glob
import hashlib
import json
import os
import random
import re
import shutil
import subprocess
import sys
import tempfile
import threading
import time
from pathlib import Path

KINDS = ("mechanical", "load", "behavioral", "trigger", "platform-fact")
REQUIRED_TOP = ("target", "target_path", "evals")
REQUIRED_EVAL = ("id", "name", "kind", "baseline", "prompt", "expected_output",
                 "files", "expectations", "added_in")

# The model every executor and grader runs on unless `init --model` names another. The full
# ID: in a headless session the `sonnet` alias has resolved to an older model
# (plugin-anatomy, references/agents.md, Model names).
DEFAULT_MODEL = "claude-sonnet-5-5"

# What a headless executor may use without asking: it has nobody to ask. The same tools a
# general-purpose subagent had when executors were spawned through the Agent tool.
EXECUTOR_TOOLS = "Bash Read Write Edit Glob Grep Agent Skill WebSearch WebFetch"
GRADER_TOOLS = "Bash Read Write Glob Grep"

# The headings of references/prompts.md the runner reads its prompts from.
PROMPT_HEADINGS = {
    "executor": "## Executor",
    "executor_no_target": "## Executor, no target",
    "grader": "## Grader",
    "grader_inline": "## Grader, no skill-creator",
}

# Search order for skill-creator, established by 0.9-evals E0.1 (the two cloud-session
# paths added 2026-09-29). The first directory
# holding both agents/grader.md and scripts/aggregate_benchmark.py wins.
SKILL_CREATOR_GLOBS = (
    "$SKILL_CREATOR_DIR",
    "~/.claude/plugins/cache/*/skill-creator/*/skills/skill-creator",
    "~/.claude/plugins/marketplaces/*/plugins/skill-creator/skills/skill-creator",
    "~/.claude/skills/skill-creator",
    "~/.claude/skills/synced/*/skill-creator",
    "/mnt/skills/*/skill-creator",
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

# Where `previous` looks for the default branch, after origin/HEAD. A clone made for one
# branch (a cloud session, a CI checkout) often has no local main and no origin/HEAD, only
# the remote-tracking branch.
DEFAULT_BRANCHES = ("main", "master", "origin/main", "origin/master")


def default_branch(root):
    r = git(root, "symbolic-ref", "--short", "refs/remotes/origin/HEAD")
    if r.returncode == 0 and r.stdout.strip():
        return r.stdout.strip()
    for name in DEFAULT_BRANCHES:
        if git(root, "rev-parse", "--verify", "--quiet", f"{name}^{{commit}}").returncode == 0:
            return name
    return None


def resolve_previous(root):
    """The commit the current work started from, and a warning or None.

    The merge-base with the default branch when HEAD is on another branch, else HEAD itself
    (the parent of uncommitted work). HEAD for want of a default branch is a guess, and it
    comes back with a warning: when the work is already committed, HEAD is the version
    under test."""
    head = git(root, "rev-parse", "HEAD").stdout.strip()
    branch = default_branch(root)
    if not branch:
        return head, ("baseline 'previous' fell back to HEAD: no default branch found "
                      f"(origin/HEAD, {', '.join(DEFAULT_BRANCHES)}). If the change under "
                      "test is already committed, HEAD is the version under test — pass "
                      "--baseline <ref>.")
    mb = git(root, "merge-base", "HEAD", branch).stdout.strip()
    if not mb:
        return head, (f"baseline 'previous' fell back to HEAD: no merge-base with {branch}. "
                      "If the change under test is already committed, HEAD is the version "
                      "under test — pass --baseline <ref>.")
    return mb, None


def plugin_pathspec(root):
    """(repo top, the plugin's repo-relative path, pathspecs for the plugin minus evals/)."""
    top = Path(git(root, "rev-parse", "--show-toplevel").stdout.strip()).resolve()
    rel = root.resolve().relative_to(top)
    evals = "evals" if str(rel) == "." else f"{rel.as_posix()}/evals"
    return top, rel, [rel.as_posix(), f":(exclude){evals}"]


def snapshot(root, ref, dest):
    """git archive the whole plugin directory at <ref> into dest, keeping repo-relative paths.

    The whole plugin, not the target's directory: a target reads its plugin's other skills,
    scripts and templates through ${CLAUDE_PLUGIN_ROOT}, and a baseline that finds only its
    own directory in the snapshot reads the rest from the working tree. `evals/` is left
    out — it holds the sets, and so the expectations, and no target reads it as plugin
    content. Returns the snapshot's plugin root.
    """
    top, rel, spec = plugin_pathspec(root)
    dest.mkdir(parents=True, exist_ok=True)
    arch = subprocess.run(["git", "archive", "--format=tar", ref, "--", *spec],
                          cwd=top, capture_output=True)
    if arch.returncode != 0:
        raise SystemExit(f"git archive {ref} {rel} failed: {arch.stderr.decode().strip()}"
                         " — if the plugin is new, the baseline is 'none'")
    tar = subprocess.run(["tar", "-x", "-C", str(dest)], input=arch.stdout, capture_output=True)
    if tar.returncode != 0:
        raise SystemExit(f"tar -x failed: {tar.stderr.decode().strip()}")
    return dest / rel


def same_as_worktree(root, ref):
    """True when the plugin (minus evals/) is the same at <ref> as in the working tree."""
    top, _, spec = plugin_pathspec(root)
    if git(top, "diff", "--quiet", ref, "--", *spec).returncode != 0:
        return False
    return not git(top, "ls-files", "--others", "--exclude-standard", "--", *spec).stdout.strip()


def write_json(path, obj):
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(json.dumps(obj, indent=2) + "\n")


def read_json(path):
    try:
        return json.loads(Path(path).read_text())
    except (OSError, json.JSONDecodeError):
        return None


def inputs_hash(root, ev):
    """A digest of everything a run of this eval is given besides the plugin itself: the
    prompt, the harness sheet and every path under `files`. Two runs at the same baseline
    ref with the same digest and model ran the same thing."""
    h = hashlib.sha256()

    def add(label, data):
        h.update(label.encode() + b"\0" + data + b"\0")

    add("prompt", ev["prompt"].encode())
    paths = ([ev["harness"]] if ev.get("harness") else []) + sorted(str(f) for f in ev.get("files", []))
    for rel in paths:
        p = root / rel
        if p.is_file():
            add(rel, p.read_bytes())
        elif p.is_dir():
            for f in sorted(x for x in p.rglob("*") if x.is_file()):
                parts = f.relative_to(root).parts
                if ".git" in parts or "__pycache__" in parts or f.name == ".DS_Store":
                    continue
                add("/".join(parts), f.read_bytes())
        else:
            add(rel, b"<missing>")
    return h.hexdigest()[:16]


def iteration_number(path):
    try:
        return int(path.name.split("-")[1])
    except (IndexError, ValueError):
        return -1


def run_finished(rdir):
    """A run whose executor finished and was not thrown away."""
    rdir = Path(rdir)
    return ((rdir / "transcript.md").is_file() and not (rdir / "not-run.json").exists()
            and ((rdir / "timing.json").is_file() or (rdir / "grading.json").is_file()))


def find_reusable(tdir, this_it, ref, ev, config, model, ihash, reuse_unhashed):
    """The newest earlier iteration's finished runs of this eval's baseline, or None.

    A baseline at a fixed ref is the same plugin every time, so its run is the same run:
    reuse needs the same ref, model and inputs digest. A manifest written before the digest
    existed has none and is passed over, unless --reuse-unhashed takes it on the prompt and
    harness path alone. Returns (run dirs, the expectations they were graded against).
    """
    want = ev.get("runs", 1)
    for it in sorted((p for p in tdir.glob("iteration-*") if p != this_it),
                     key=iteration_number, reverse=True):
        m = read_json(it / "manifest.json")
        if not m or (m.get("baseline_ref") or None) != ref:
            continue
        if m.get("model", DEFAULT_MODEL) != model:
            continue
        entries = [r for r in m.get("runs", [])
                   if r.get("eval_id") == ev["id"] and r.get("config") == config]
        if len(entries) < want:
            continue
        first = entries[0]
        if "inputs_hash" in first:
            if first["inputs_hash"] != ihash:
                continue
        elif not (reuse_unhashed and first.get("prompt") == ev["prompt"]
                  and Path(first.get("harness") or "").name == Path(ev.get("harness") or "").name):
            continue
        dirs = []
        for e in entries[:want]:
            d = Path(e["run_dir"])
            try:        # the iteration may have moved with its worktree since
                d = it / d.relative_to(m["iteration"])
            except (KeyError, ValueError):
                pass
            dirs.append(d)
        if all(run_finished(d) for d in dirs):
            return dirs, first.get("expectations")
    return None


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

    model = args.model or DEFAULT_MODEL
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
    warnings = []
    if base == "none":
        base_config, ref = "without_skill", None
    else:
        ref, warning = resolve_previous(root) if base == "previous" else (base, None)
        if warning:
            warnings.append(warning)
        ref = git(root, "rev-parse", "--short", f"{ref}^{{commit}}").stdout.strip()
        base_config = "old_skill"
        top, rel, _ = plugin_pathspec(root)
        at_ref = (rel / data["target_path"]).as_posix()
        if git(top, "cat-file", "-e", f"{ref}:{at_ref}").returncode != 0:
            shutil.rmtree(it)
            print(f"{data['target_path']} does not exist at {ref}"
                  " — if the target is new, its baseline is 'none'")
            return 1

    # Which baselines an earlier iteration already ran, which this one runs, and which a
    # working-tree-only iteration goes without.
    hashes = {ev["id"]: inputs_hash(root, ev) for ev in evals}
    reused, to_run, absent = {}, [], []
    for ev in evals:
        hit = None if args.no_reuse else find_reusable(
            tdir, it, ref, ev, base_config, model, hashes[ev["id"]], args.reuse_unhashed)
        if hit:
            reused[ev["id"]] = hit
        elif args.working_tree_only:
            absent.append(ev["id"])
        else:
            to_run.append(ev["id"])

    base_root = base_file = None
    if to_run and base_config == "old_skill":
        base_root = snapshot(root, ref, it / "baseline-snapshot")
        base_file = base_root / data["target_path"]
        if same_as_worktree(root, ref):
            warnings.append(f"the baseline {ref} is identical to the working tree outside "
                            "evals/: both configurations run the same files. If the change "
                            "under test is already committed, pass --baseline <ref>.")
    if absent:
        warnings.append(f"working tree only: eval(s) {absent} have no finished baseline run "
                        f"at {ref or 'none'} to reuse, so their report has no baseline "
                        "column. A failed expectation there is rerun without "
                        "--working-tree-only to see whether the baseline fails it too.")

    runs = []
    for ev in evals:
        edir = it / f"eval-{ev['id']}-{ev['name']}"
        meta = {"eval_id": ev["id"], "eval_name": ev["name"], "prompt": ev["prompt"],
                "assertions": ev["expectations"]}
        write_json(edir / "eval_metadata.json", meta)
        harness = str(root / ev["harness"]) if ev.get("harness") else None
        configs = [("with_skill", target_file, root)]
        if ev["id"] not in absent:
            configs.append((base_config, base_file, base_root))
        for config, tfile, proot in configs:
            write_json(edir / config / "eval_metadata.json", meta)
            from_dirs, graded_against = (reused.get(ev["id"]) or (None, None)) \
                if config == base_config else (None, None)
            for k in range(1, ev.get("runs", 1) + 1):
                rdir = edir / config / f"run-{k}"
                entry = {
                    "eval_id": ev["id"], "name": ev["name"], "config": config,
                    "run_dir": str(rdir), "outputs_dir": str(rdir / "outputs"),
                    "prompt": ev["prompt"], "harness": harness,
                    "target_file": str(tfile) if tfile else None,
                    "plugin_root": str(proot) if proot else None,
                    "expectations": ev["expectations"],
                    "inputs_hash": hashes[ev["id"]],
                    "reused_from": None,
                }
                if from_dirs:
                    # The whole run directory, so the iteration stands alone for the
                    # benchmark and the viewer. Its grades hold only for the expectations
                    # it was graded against; changed ones are graded again, not rerun.
                    shutil.copytree(from_dirs[k - 1], rdir)
                    (rdir / "outputs").mkdir(exist_ok=True)
                    if graded_against != ev["expectations"]:
                        (rdir / "grading.json").unlink(missing_ok=True)
                    if not (rdir / "timing.json").is_file():
                        write_json(rdir / "timing.json", {"total_tokens": 0, "duration_ms": 0,
                                                          "total_duration_seconds": 0.0})
                    entry["reused_from"] = str(from_dirs[k - 1])
                    entry["target_file"] = entry["plugin_root"] = None
                else:
                    (rdir / "outputs").mkdir(parents=True)
                runs.append(entry)

    manifest = {"iteration": str(it), "target": args.target, "plugin_dir": str(root),
                "model": model, "baseline_ref": ref,
                "working_tree_only": bool(args.working_tree_only),
                # Without the runner: plugin-dev's Agent guard lets these runs be spawned.
                "by_hand": bool(args.by_hand),
                "baseline_plugin_root": str(base_root) if base_root else None,
                "warnings": warnings,
                "skill_creator": locate_skill_creator(), "runs": runs}
    write_json(it / "manifest.json", manifest)
    if args.quiet:
        # What the calling chat needs: where the iteration is and what to settle first. The
        # runs, with their prompts and expectations, are the runner's to read.
        owed = [r for r in runs if not r["reused_from"]]
        print(json.dumps({"iteration": str(it), "baseline_ref": ref, "model": model,
                          "executors_to_run": len(owed),
                          "baseline_runs_reused": len(runs) - len(owed),
                          "evals_without_baseline": absent, "warnings": warnings}, indent=2))
    else:
        print(json.dumps(manifest, indent=2))
    for line in warnings:
        print(f"warning: {line}", file=sys.stderr)
    return 0


# ---------------------------------------------------------------- run

def load_prompts():
    """The fenced block under each heading of references/prompts.md, the one copy."""
    path = Path(__file__).resolve().parent.parent / "references" / "prompts.md"
    text = path.read_text()
    prompts = {}
    for key, heading in PROMPT_HEADINGS.items():
        m = re.search(r"^" + re.escape(heading) + r"\n.*?^```text\n(.*?)\n```",
                      text, re.S | re.M)
        if not m:
            raise SystemExit(f"{path}: no ```text block under '{heading}'")
        prompts[key] = m.group(1)
    return prompts


def fill(template, values, payload):
    """Fill every <name> of `values`, refuse a template that still holds one of ours, then
    fill `payload` — the eval's own text, which may contain angle brackets of its own."""
    out = template
    for name, value in values.items():
        out = out.replace(f"<{name}>", value)
    left = sorted(set(re.findall(r"<[a-z][a-z_ -]*>", out)) - {f"<{k}>" for k in payload})
    if left:
        raise SystemExit(f"prompts.md: nothing fills {', '.join(left)}")
    for name, value in payload.items():
        out = out.replace(f"<{name}>", value)
    return out


def claude_bin():
    return os.environ.get("RUN_EVALS_CLAUDE") or shutil.which("claude")


def read_stream(path):
    """(the session's last result record or None, every tool call's input as text)."""
    result, calls = None, []
    try:
        lines = Path(path).read_text(errors="replace").splitlines()
    except OSError:
        return None, calls
    for line in lines:
        try:
            rec = json.loads(line)
        except json.JSONDecodeError:
            continue
        if not isinstance(rec, dict):
            continue
        if rec.get("type") == "result":
            result = rec
        content = (rec.get("message") or {}).get("content")
        if rec.get("type") == "assistant" and isinstance(content, list):
            calls += [json.dumps(b.get("input", {})) for b in content
                      if isinstance(b, dict) and b.get("type") == "tool_use"]
    return result, calls


def session(claude, prompt, model, tools, cwd, add_dirs, log_path, timeout):
    """One headless session. Returns {"error": why} or {"result": record, "calls": [...],
    "duration_ms": wall time}. The stream is kept at log_path."""
    cmd = [claude, "-p", prompt, "--model", model, "--output-format", "stream-json",
           "--verbose", "--permission-mode", "acceptEdits", "--allowedTools", tools]
    for d in add_dirs:
        cmd += ["--add-dir", str(d)]
    # A session started from inside Claude Code refuses to nest unless this is unset.
    env = {k: v for k, v in os.environ.items() if k != "CLAUDECODE"}
    start = time.time()
    try:
        with open(log_path, "w") as out:
            proc = subprocess.run(cmd, cwd=cwd, env=env, stdin=subprocess.DEVNULL,
                                  stdout=out, stderr=subprocess.PIPE, text=True,
                                  timeout=timeout)
    except subprocess.TimeoutExpired:
        return {"error": f"timed out after {timeout}s"}
    except OSError as e:
        return {"error": f"could not start {claude}: {e}"}
    result, calls = read_stream(log_path)
    if result is None:
        tail = (proc.stderr or "").strip().splitlines()[-1:] or ["no output"]
        return {"error": f"no result record (exit {proc.returncode}): {tail[0][:300]}"}
    if result.get("is_error") or proc.returncode != 0:
        return {"error": f"session error (exit {proc.returncode}): "
                         f"{str(result.get('result') or result.get('subtype'))[:300]}"}
    return {"result": result, "calls": calls, "duration_ms": int((time.time() - start) * 1000)}


def usage_tokens(result):
    u = result.get("usage") or {}
    return sum(int(u.get(k) or 0) for k in ("input_tokens", "output_tokens",
                                             "cache_creation_input_tokens",
                                             "cache_read_input_tokens"))


def timing_record(res, attempts):
    r = res["result"]
    return {"total_tokens": usage_tokens(r), "duration_ms": res["duration_ms"],
            "total_duration_seconds": round(res["duration_ms"] / 1000, 1),
            "usage": r.get("usage"), "cost_usd": r.get("total_cost_usd"),
            "num_turns": r.get("num_turns"), "attempts": attempts}


def read_what_it_is_graded_on(calls, run, manifest):
    """The first path a tool call named that holds expectations, or None.

    The manifest, both copies of eval_metadata.json, the set, and every other run's
    directory hold what a run is graded on (eval-kinds.md, Harness rules)."""
    it, plugin_dir = manifest["iteration"], manifest.get("plugin_dir") or ""
    # A path is named in full, or relative to the plugin directory the session runs in. A
    # relative one starts a word: `outputs/evals/sets/x.json` in a fixture copy is not it.
    def either(path):
        rel = os.path.relpath(path, plugin_dir) if plugin_dir else path
        return "(?:" + re.escape(path) + r"|(?<![\w/.-])" + re.escape(rel) + ")"

    set_file = os.path.join(plugin_dir, "evals", "sets", f"{manifest.get('target', '')}.json")
    in_iteration = re.compile(either(it) + r"/(manifest\.json|eval-[^\s\"'\\]*)")
    the_set = re.compile(either(set_file) + r"(?![\w.-])")
    own = os.path.relpath(run["run_dir"], it)
    for text in calls:
        if the_set.search(text):
            return set_file
        for m in in_iteration.finditer(text):
            if not m.group(1).startswith(own):
                return os.path.join(it, m.group(1))
    return None


class Progress:
    def __init__(self, it):
        self.path, self.lock = Path(it) / "run.log", threading.Lock()

    def __call__(self, line):
        with self.lock, open(self.path, "a") as f:
            f.write(f"{time.strftime('%H:%M:%S')} {line}\n")


def execute(run, ctx):
    """Run one executor; an attempt that errors or reads its expectations is thrown away
    and run once more (SKILL.md, The behavioral loop). Two bad attempts leave not-run.json."""
    rdir = Path(run["run_dir"])
    label = f"eval {run['eval_id']} {run['config']} {rdir.name}"
    why = None
    for attempt in (1, 2):
        scratch = tempfile.mkdtemp(prefix=f"run-evals-{ctx['target']}-")
        template = ctx["prompts"]["executor" if run.get("target_file") else "executor_no_target"]
        prompt = fill(template, {
            "target": ctx["target"], "target_file": run.get("target_file") or "",
            "repo root": ctx["repo_root"], "plugin_root": run.get("plugin_root") or "",
            "harness": run.get("harness") or "no harness file",
            "outputs_dir": run["outputs_dir"], "iteration": ctx["iteration"],
            "run_dir": run["run_dir"], "plugin dir": ctx["plugin_dir"], "scratch": scratch,
        }, {"prompt": run["prompt"]})
        res = session(ctx["claude"], prompt, ctx["model"], EXECUTOR_TOOLS, ctx["plugin_dir"],
                      [scratch], rdir / "session.jsonl", ctx["timeout"])
        why = res.get("error")
        if not why:
            seen = read_what_it_is_graded_on(res["calls"], run, ctx["manifest"])
            why = f"void: a tool call named {seen}" if seen else None
        if not why:
            write_json(rdir / "timing.json", timing_record(res, attempt))
            ctx["progress"](f"executed {label} ({usage_tokens(res['result'])} tokens)")
            return
        ctx["progress"](f"attempt {attempt} thrown away, {label}: {why}")
        shutil.rmtree(rdir / "outputs", ignore_errors=True)
        (rdir / "outputs").mkdir(parents=True, exist_ok=True)
        (rdir / "transcript.md").unlink(missing_ok=True)
    write_json(rdir / "not-run.json", {"error": why, "attempts": 2})


def graded(rdir):
    g = read_json(Path(rdir) / "grading.json")
    exps = g.get("expectations") if isinstance(g, dict) else None
    if isinstance(exps, list) and exps and all(isinstance(e, dict) and "passed" in e for e in exps):
        return g
    return None


def grade(run, ctx):
    rdir = Path(run["run_dir"])
    label = f"eval {run['eval_id']} {run['config']} {rdir.name}"
    sc = ctx["manifest"].get("skill_creator")
    prompt = fill(ctx["prompts"]["grader" if sc else "grader_inline"],
                  {"skill-creator": sc or "", "run_dir": run["run_dir"]},
                  {"expectations": json.dumps(run["expectations"])})
    why = None
    for attempt in (1, 2):
        (rdir / "grading.json").unlink(missing_ok=True)
        res = session(ctx["claude"], prompt, ctx["model"], GRADER_TOOLS, ctx["plugin_dir"],
                      [sc] if sc else [], rdir / "grader.jsonl", ctx["timeout"])
        why = res.get("error") or (None if graded(rdir) else "no usable grading.json")
        if not why:
            write_json(rdir / "grader-timing.json", timing_record(res, attempt))
            ctx["progress"](f"graded {label}")
            return
        ctx["progress"](f"grader attempt {attempt} failed, {label}: {why}")
    (rdir / "grading.json").unlink(missing_ok=True)
    write_json(rdir / "not-graded.json", {"error": why, "attempts": 2})


def cmd_run(args):
    it = Path(args.iteration).resolve()
    manifest = read_json(it / "manifest.json")
    if not manifest:
        print(f"no manifest.json in {it} — run `init` first", file=sys.stderr)
        return 2
    plugin_dir = manifest.get("plugin_dir") or str(plugin_root(it) or "")
    top = git(plugin_dir, "rev-parse", "--show-toplevel").stdout.strip() if plugin_dir else ""
    ctx = {
        "manifest": manifest, "iteration": str(it), "plugin_dir": plugin_dir,
        "repo_root": top or plugin_dir, "target": manifest.get("target") or it.parent.name,
        "model": manifest.get("model") or DEFAULT_MODEL, "timeout": args.timeout,
        "prompts": load_prompts(), "claude": claude_bin(), "progress": Progress(it),
    }
    runs = manifest["runs"]

    def done(r, name):
        return (Path(r["run_dir"]) / name).exists()

    # Whatever an earlier `run` of this iteration could not finish — a session limit, an
    # outage — is owed again: running `run` a second time is the retry.
    to_execute = [r for r in runs if not r.get("reused_from") and not done(r, "timing.json")]
    will_grade = [r for r in runs if not graded(r["run_dir"])]
    if args.dry_run:
        for r in to_execute:
            print(f"execute  eval {r['eval_id']} {r['config']}  {r['run_dir']}")
        for r in will_grade:
            print(f"grade    eval {r['eval_id']} {r['config']}  {r['run_dir']}")
        reused = sum(1 for r in runs if r.get("reused_from"))
        print(f"{len(to_execute)} executor(s) and {len(will_grade)} grader(s) on {ctx['model']}, "
              f"{args.jobs} at once; {reused} baseline run(s) reused; claude: {ctx['claude']}")
        return 0
    if not ctx["claude"]:
        print("no `claude` on PATH (or in RUN_EVALS_CLAUDE): the runner cannot start a "
              "headless session — see SKILL.md, Without the runner", file=sys.stderr)
        return 2

    for r in runs:
        for marker in ("not-run.json", "not-graded.json"):
            (Path(r["run_dir"]) / marker).unlink(missing_ok=True)
    start = time.time()
    with concurrent.futures.ThreadPoolExecutor(max_workers=max(1, args.jobs)) as pool:
        # Every executor finishes before any grader starts: a grader's prompt holds the
        # expectations, and nothing that does exists while an executor could read it.
        list(pool.map(lambda r: execute(r, ctx), to_execute))
        to_grade = [r for r in runs if not done(r, "not-run.json") and not graded(r["run_dir"])]
        list(pool.map(lambda r: grade(r, ctx), to_grade))
    finalize(it)
    write_json(it / "run-summary.json", {
        "executed": len(to_execute), "graded": len(to_grade),
        "wall_seconds": round(time.time() - start, 1)})
    return cmd_report(argparse.Namespace(iteration=str(it)))


# ---------------------------------------------------------------- report

def clip(text, n):
    text = " ".join(str(text).split())
    return text if len(text) <= n else text[:n - 1] + "…"


def cmd_report(args):
    """One table per iteration, and under it only what needs reading: each expectation the
    working tree failed with the grader's evidence and what the baseline did with it, the
    graders' remarks on the expectations themselves, and what the iteration cost."""
    it = Path(args.iteration).resolve()
    manifest = read_json(it / "manifest.json")
    if not manifest:
        print(f"no manifest.json in {it}", file=sys.stderr)
        return 2
    evals, order = {}, []
    spent = {"executor": [0, 0, 0.0], "grader": [0, 0, 0.0]}     # sessions, tokens, cost
    for r in manifest["runs"]:
        rdir = Path(r["run_dir"])
        e = evals.setdefault(r["eval_id"], {"name": r["name"], "configs": {}})
        if r["eval_id"] not in order:
            order.append(r["eval_id"])
        c = e["configs"].setdefault(r["config"], {"passed": 0, "total": 0, "exps": [],
                                                  "notes": [], "feedback": []})
        if r.get("reused_from"):
            c["notes"].append("reused")
        for name, kind in (("timing.json", "executor"), ("grader-timing.json", "grader")):
            t = read_json(rdir / name)
            if t and not (kind == "executor" and r.get("reused_from")):
                spent[kind][0] += 1
                spent[kind][1] += int(t.get("total_tokens") or 0)
                spent[kind][2] += float(t.get("cost_usd") or 0)
        not_run = read_json(rdir / "not-run.json")
        if not_run:
            c["notes"].append(f"not run: {clip(not_run.get('error'), 120)}")
            continue
        g = graded(rdir)
        if not g:
            c["notes"].append("not graded")
            continue
        for x in g["expectations"]:
            c["total"] += 1
            c["passed"] += 1 if x.get("passed") else 0
            c["exps"].append(x)
        fb = g.get("eval_feedback") or {}
        c["feedback"] += [s for s in fb.get("suggestions", []) if isinstance(s, dict)]

    base_names = sorted({c for e in evals.values() for c in e["configs"]} - {"with_skill"})
    base = base_names[0] if base_names else None
    out = [f"# {manifest.get('target') or it.parent.name} {it.name}",
           "",
           f"Baseline: {manifest.get('baseline_ref') or 'none'}"
           f"{' · working tree only' if manifest.get('working_tree_only') else ''}"
           f" · model: {manifest.get('model') or DEFAULT_MODEL}",
           "",
           f"| Eval | with_skill | {base or 'baseline'} |", "|---|---|---|"]

    def cell(c):
        if c is None:
            return "—"
        text = f"{c['passed']}/{c['total']}" if c["total"] else "—"
        notes = sorted(set(c["notes"]))
        return text + (f" ({'; '.join(notes)})" if notes else "")

    totals = {"with_skill": [0, 0], base: [0, 0]}
    incomplete = False
    for eid in order:
        e = evals[eid]
        w, b = e["configs"].get("with_skill"), e["configs"].get(base) if base else None
        out.append(f"| {eid} `{e['name']}` | {cell(w)} | {cell(b)} |")
        for name, c in (("with_skill", w), (base, b)):
            if c:
                totals[name][0] += c["passed"]
                totals[name][1] += c["total"]
                incomplete |= any(n.startswith("not") for n in c["notes"])

    def rate(pair):
        return f"{pair[0]}/{pair[1]} ({100 * pair[0] / pair[1]:.1f}%)" if pair[1] else "—"

    out += ["", f"**Pass rate:** {rate(totals['with_skill'])} vs {rate(totals[base]) if base else '—'}"]

    failed, base_only, remarks = [], [], []
    for eid in order:
        e = evals[eid]
        w, b = e["configs"].get("with_skill"), e["configs"].get(base) if base else None
        theirs = {x.get("text"): x.get("passed") for x in (b["exps"] if b else [])}
        mine = {x.get("text"): x.get("passed") for x in (w["exps"] if w else [])}
        for i, x in enumerate(w["exps"] if w else [], 1):
            if not x.get("passed"):
                was = theirs.get(x.get("text"))
                was = "not run" if was is None else ("passed" if was else "failed")
                failed.append(f"- eval {eid}, expectation {i} (baseline: {was}): "
                              f"{clip(x.get('text'), 220)} — {clip(x.get('evidence'), 320)}")
        for text, ok in theirs.items():
            if not ok and mine.get(text):
                base_only.append(f"- eval {eid}: {clip(text, 160)}")
        seen = set()
        for s in (w["feedback"] if w else []) + (b["feedback"] if b else []):
            key = clip(s.get("assertion") or s.get("reason"), 60)
            if key in seen or len(seen) >= 3:
                continue
            seen.add(key)
            about = f"“{clip(s['assertion'], 90)}”: " if s.get("assertion") else ""
            remarks.append(f"- eval {eid}: {about}{clip(s.get('reason'), 240)}")
    out += ["", "## Expectations the working tree failed", ""] + (failed or ["None."])
    if base:
        out += ["", "## Expectations only the baseline failed", ""] + (base_only or ["None."])
    out += ["", "## Graders on the expectations themselves", ""] + (remarks or ["None."])
    summary = read_json(it / "run-summary.json") or {}
    wall = f"; wall time {summary['wall_seconds']}s" if summary.get("wall_seconds") else ""

    def spent_line(label, s):
        cost = f", ${s[2]:.2f}" if s[2] else ""
        return f"- {label}: {s[0]} session(s), {s[1]:,} tokens{cost}"

    reused = sum(1 for r in manifest["runs"] if r.get("reused_from"))
    out += ["", "## Cost", "",
            spent_line("executors", spent["executor"])
            + f"; {reused} baseline run(s) reused from earlier iterations",
            spent_line("graders", spent["grader"]),
            "- tokens count every turn's input, cache reads included" + wall]
    text = "\n".join(out) + "\n"
    (it / "report.md").write_text(text)
    print(text, end="")
    return 1 if incomplete else 0


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
    fixed, missing = finalize(Path(args.iteration))
    for line in missing:
        print(line)
    print(f"{fixed} grading.json file(s) now defer to timing.json")
    return 1 if missing else 0


def finalize(it):
    fixed, missing = 0, []
    for rdir in sorted(it.glob("eval-*/*/run-*")):
        grading, timing = rdir / "grading.json", rdir / "timing.json"
        if (rdir / "not-run.json").exists():
            continue
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
    return fixed, missing


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


# ---------------------------------------------------------------- blind

# An expectation that can only be checked in the transcript names it (SKILL.md, The set).
NEEDS_TRANSCRIPT = re.compile(r"transcript", re.IGNORECASE)


def cmd_blind(args):
    """Stage each eval's two configurations as A and B in a random order.

    The comparator is told nothing but the two directories, so which one is the working
    tree's lives only in `blind/key.json` — written here, read after the verdicts, and never
    part of what this prints. It sees `outputs/` and no transcript, so an expectation that
    names the transcript would fail for both sides there: those are withheld, and counted in
    `withheld_expectations`.
    """
    it = Path(args.iteration).resolve()
    if not it.is_dir():
        print(f"no iteration at {it}", file=sys.stderr)
        return 1
    # expected_output lives in the set, not in the iteration's eval_metadata.json.
    expected, root = {}, plugin_root(it)
    if root:
        set_path = root / "evals" / "sets" / f"{it.parent.name}.json"
        if set_path.is_file():
            try:
                expected = {e.get("id"): e.get("expected_output", "")
                            for e in json.loads(set_path.read_text()).get("evals", [])}
            except (OSError, json.JSONDecodeError):
                pass

    pairs, skipped = [], []
    for edir in sorted(it.glob("eval-*")):
        outs = {d.name: d / "run-1" / "outputs" for d in sorted(edir.iterdir())
                if d.is_dir() and d.name != "blind" and (d / "run-1" / "outputs").is_dir()}
        base = next((c for c in outs if c != "with_skill"), None)
        if "with_skill" not in outs or base is None:
            skipped.append(f"{edir.name}: needs with_skill and a baseline with run-1/outputs")
            continue
        meta = {}
        if (edir / "eval_metadata.json").is_file():
            meta = json.loads((edir / "eval_metadata.json").read_text())
        blind_dir = edir / "blind"
        if blind_dir.exists():
            shutil.rmtree(blind_dir)
        order = ["with_skill", base]
        random.shuffle(order)
        for label, config in zip(("A", "B"), order):
            shutil.copytree(outs[config], blind_dir / label)
        write_json(blind_dir / "key.json", {"A": order[0], "B": order[1]})
        assertions = meta.get("assertions", [])
        visible = [a for a in assertions if not NEEDS_TRANSCRIPT.search(str(a))]
        pairs.append({
            "eval": edir.name,
            "a_dir": str(blind_dir / "A"),
            "b_dir": str(blind_dir / "B"),
            "prompt": meta.get("prompt", ""),
            "expected_output": expected.get(meta.get("eval_id"), ""),
            "expectations": visible,
            "withheld_expectations": len(assertions) - len(visible),
        })

    for line in skipped:
        print(line, file=sys.stderr)
    print(json.dumps(pairs, indent=2))
    return 0 if pairs else 1


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
    i.add_argument("--working-tree-only", action="store_true",
                   help="run no baseline executor; a baseline an earlier iteration finished is still reused")
    i.add_argument("--no-reuse", action="store_true",
                   help="run every baseline again, whatever earlier iterations hold")
    i.add_argument("--reuse-unhashed", action="store_true",
                   help="also reuse baselines from manifests written before inputs_hash existed, "
                        "matched on prompt and harness name")
    i.add_argument("--by-hand", action="store_true",
                   help="the runs will be spawned through the Agent tool (SKILL.md, Without the runner)")
    i.add_argument("--quiet", "-q", action="store_true",
                   help="print the iteration path, the counts and the warnings, not the whole manifest")
    i.add_argument("--model", help=f"the model every executor and grader runs on (default {DEFAULT_MODEL})")
    i.set_defaults(fn=cmd_init)
    rn = sub.add_parser("run")
    rn.add_argument("iteration")
    rn.add_argument("--jobs", type=int, default=6, help="sessions running at once (default 6)")
    rn.add_argument("--timeout", type=int, default=2700, help="seconds one session may take (default 2700)")
    rn.add_argument("--dry-run", action="store_true", help="print what would run and start nothing")
    rn.set_defaults(fn=cmd_run)
    rp = sub.add_parser("report")
    rp.add_argument("iteration")
    rp.set_defaults(fn=cmd_report)
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
    b = sub.add_parser("blind")
    b.add_argument("iteration")
    b.set_defaults(fn=cmd_blind)
    loc = sub.add_parser("locate-skill-creator")
    loc.set_defaults(fn=cmd_locate)
    args = ap.parse_args()
    sys.exit(args.fn(args))


if __name__ == "__main__":
    main()
