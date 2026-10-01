#!/usr/bin/env python3
"""Turn one headless run-package session into the outputs its harness sheet lists.

Usage: post.py <run dir> <repo copy>

Reads `<run dir>/stream.jsonl` (the session's `--output-format stream-json --verbose`
record), `<run dir>/runner.json` (written by run.sh), the session's subagent transcripts
(`~/.claude/projects/*/<session id>/subagents/agent-*.jsonl` and their `.meta.json`), and the
copy, read-only. Writes, under `<run dir>`:

- `transcript.md` — the driver's (main thread's) every text and tool call in order, each tool
  call with its input and its result, then the final message, then `--- harness copies ---`
  and what this script copied.
- `outputs/summary.md` — the session's final message (the `result` event's text), verbatim.
- `outputs/spawns.md` — every main-thread Agent call: index, batch (one assistant message id is
  one batch), `subagent_type`, `run_in_background`, the `Section:`, `Scaffold:`, `Round:`,
  `Focus:` and `Letter:` lines, the prompt verbatim, and the return's first line (the whole
  return when it is `design-gap` or `spec-change`); between batches, each `status.py` run.
- `outputs/status-log.txt` — every main-thread Bash call that runs `status.py`, with its
  output; `outputs/status-final.txt` — `status.py <pkg>` run once more, with the session's
  plugin.
- `outputs/driver-bash.md` — every main-thread Bash command, in order.
- `outputs/returns.md` — per agent run: role, its `Section:` or `Scaffold:` line, the first line
  of the report its caller received, and the first line of its last assistant text.
- `outputs/git-log.txt` (`git log --format='%H%n%B' --stat <seed>..HEAD`), `outputs/git-oneline.txt`
  (`git log --format='%h %s'`), `outputs/git-status.txt` (`git status --porcelain`).
- `outputs/repo/` — the copy's `docs/`, `tests/`, `packages/` and `.dev-team/{gate,stop}/`.
- `outputs/gates.md` — every gate-record version in `outputs/gate-history/` and every final
  record: header and modification time; per batch holding two or more implementers, each
  one's gate window and an `F4:` line.
- `outputs/cost.json` — the `result` event's cost, duration and per-model usage, and the model
  every assistant record names.

Nothing it writes holds an expectation. Standard library only.
"""

from __future__ import annotations

import glob
import json
import os
import re
import subprocess
import sys
from datetime import datetime, timezone
from pathlib import Path

FIELDS = ("Section:", "Scaffold:", "Round:", "Focus:", "Letter:")


def load_stream(path: Path) -> list[dict]:
    events = []
    for line in path.read_text(errors="replace").splitlines():
        line = line.strip()
        if not line:
            continue
        try:
            events.append(json.loads(line))
        except json.JSONDecodeError:
            continue
    return events


def result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        parts = []
        for c in content:
            if isinstance(c, dict) and c.get("type") == "text":
                parts.append(c.get("text", ""))
        return "\n".join(parts)
    return ""


FRAME = "[Subagent hand-back]"


def report(text: str) -> str:
    """The agent's report as its caller received it, without the platform's hand-back frame.

    Claude Code wraps a SubagentHandback report in a paragraph that starts `[Subagent
    hand-back]`, ends `The report follows:`, and indents every line of the report.
    """
    if not text.lstrip().startswith(FRAME):
        return text
    _, _, rest = text.partition("The report follows:")
    lines = rest.splitlines()
    while lines and not lines[0].strip():
        lines.pop(0)
    indent = min((len(l) - len(l.lstrip()) for l in lines if l.strip()), default=0)
    return "\n".join(l[indent:] for l in lines)


def first_line(text: str) -> str:
    text = report(text)
    for line in text.splitlines():
        if line.strip():
            return line.strip()
    return ""


def git(copy: Path, *args: str) -> str:
    r = subprocess.run(["git", "-C", str(copy), *args], capture_output=True, text=True)
    return r.stdout + (r.stderr if r.returncode else "")


def subagent_transcripts(session_id: str) -> dict[str, dict]:
    """toolUseId -> {agent_type, path, last_text, first_ts, last_ts, records}."""
    out: dict[str, dict] = {}
    pattern = os.path.expanduser(f"~/.claude/projects/*/{session_id}/subagents/agent-*.meta.json")
    for meta_path in glob.glob(pattern):
        try:
            meta = json.load(open(meta_path))
        except (OSError, json.JSONDecodeError):
            continue
        jsonl = meta_path[: -len(".meta.json")] + ".jsonl"
        last_text, stamps = "", []
        assistant_stamps = []
        try:
            for line in open(jsonl, errors="replace"):
                try:
                    rec = json.loads(line)
                except json.JSONDecodeError:
                    continue
                ts = rec.get("timestamp")
                if ts:
                    stamps.append(ts)
                if rec.get("type") == "assistant":
                    if ts:
                        assistant_stamps.append(ts)
                    text = result_text(rec.get("message", {}).get("content"))
                    if text.strip():
                        last_text = text
        except OSError:
            continue
        out[meta.get("toolUseId", jsonl)] = {
            "agent_type": meta.get("agentType", "?"),
            "path": jsonl,
            "last_text": last_text,
            "first_ts": stamps[0] if stamps else None,
            "last_ts": stamps[-1] if stamps else None,
            "assistant_stamps": assistant_stamps,
        }
    return out


def parse_ts(ts: str | None) -> float | None:
    if not ts:
        return None
    try:
        return datetime.fromisoformat(ts.replace("Z", "+00:00")).timestamp()
    except ValueError:
        return None


def stamp(epoch: float) -> str:
    return datetime.fromtimestamp(epoch, tz=timezone.utc).strftime("%Y-%m-%dT%H:%M:%SZ")


def main() -> int:
    if len(sys.argv) != 3:
        print("usage: post.py <run dir> <repo copy>", file=sys.stderr)
        return 2
    run_dir, copy = Path(sys.argv[1]).resolve(), Path(sys.argv[2]).resolve()
    outputs = run_dir / "outputs"
    outputs.mkdir(parents=True, exist_ok=True)
    runner = json.loads((run_dir / "runner.json").read_text())
    plugin_dir = runner["plugin_dir"]
    pkg = runner["command"].split()[1]
    events = load_stream(run_dir / "stream.jsonl")

    session_id, models, result = None, set(), None
    calls: list[dict] = []          # main-thread tool calls, in order
    by_id: dict[str, dict] = {}
    texts: list[tuple[int, str]] = []  # (position, main-thread text)
    order = 0
    for ev in events:
        t = ev.get("type")
        if t == "system" and ev.get("subtype") == "init":
            session_id = ev.get("session_id")
        if t == "result":
            result = ev
        if t == "assistant":
            msg = ev.get("message", {})
            if msg.get("model"):
                models.add(msg["model"])
            if ev.get("parent_tool_use_id"):
                continue
            for c in msg.get("content", []) or []:
                order += 1
                if c.get("type") == "text" and c.get("text", "").strip():
                    texts.append((order, c["text"]))
                    calls.append({"pos": order, "kind": "text", "text": c["text"]})
                elif c.get("type") == "tool_use":
                    call = {"pos": order, "kind": "tool", "id": c.get("id"), "name": c.get("name"),
                            "input": c.get("input", {}), "message_id": msg.get("id"), "result": None}
                    calls.append(call)
                    by_id[c.get("id")] = call
        if t == "user":
            if ev.get("parent_tool_use_id"):
                continue
            content = ev.get("message", {}).get("content")
            if isinstance(content, list):
                for c in content:
                    if isinstance(c, dict) and c.get("type") == "tool_result":
                        call = by_id.get(c.get("tool_use_id"))
                        if call is not None:
                            call["result"] = result_text(c.get("content"))
                            call["is_error"] = bool(c.get("is_error"))

    final = (result or {}).get("result", "") if result else ""
    if not final and texts:
        final = texts[-1][1]
    (outputs / "summary.md").write_text(final.rstrip("\n") + "\n")

    subs = subagent_transcripts(session_id) if session_id else {}

    # --- spawns.md, status-log.txt, driver-bash.md ---
    tools = [c for c in calls if c["kind"] == "tool"]
    batch_of: dict[str, int] = {}
    spawn_lines, status_log, bash_lines = ["# Spawns", ""], [], ["# Driver Bash commands", ""]
    index, last_batch = 0, None
    for c in tools:
        name, inp = c["name"], c["input"]
        if name == "Bash":
            cmd = inp.get("command", "")
            bash_lines.append(f"- `{cmd}`")
            if "status.py" in cmd:
                status_log.append(f"$ {cmd}\n{c.get('result') or ''}".rstrip() + "\n")
                spawn_lines.append(f"_status.py run: `{cmd}`_")
                spawn_lines.append("")
        if name in ("Agent", "Task"):
            mid = c.get("message_id") or c["id"]
            if mid not in batch_of:
                batch_of[mid] = len(batch_of) + 1
            batch = batch_of[mid]
            if batch != last_batch:
                spawn_lines += [f"## Batch {batch}", ""]
                last_batch = batch
            index += 1
            prompt = inp.get("prompt", "")
            ret = c.get("result") or ""
            head = first_line(ret)
            whole = ("design-gap" in head or "spec-change" in head)
            spawn_lines.append(f"### {index}. batch {batch} — `{inp.get('subagent_type', '(none)')}`")
            spawn_lines.append(f"- run_in_background: `{inp.get('run_in_background', 'not set')}`")
            for line in prompt.splitlines():
                if line.startswith(FIELDS):
                    spawn_lines.append(f"- {line}")
            spawn_lines.append("- prompt:")
            spawn_lines += ["", "```", prompt, "```", ""]
            if whole:
                spawn_lines += ["- return (whole):", "", "```", report(ret), "```", ""]
            else:
                spawn_lines.append(f"- return first line: `{head}`" if c.get("result") is not None
                                   else "- return: none recorded")
                spawn_lines.append("")
    if index == 0:
        spawn_lines.append("no Agent call")
    (outputs / "spawns.md").write_text("\n".join(spawn_lines) + "\n")
    (outputs / "status-log.txt").write_text("\n".join(status_log))
    (outputs / "driver-bash.md").write_text("\n".join(bash_lines) + "\n")

    # --- returns.md ---
    rows = ["# Returns", "", "| # | role | section | report received (first line) | last assistant text (first line) |",
            "|---|---|---|---|---|"]
    n = 0
    for c in tools:
        if c["name"] not in ("Agent", "Task"):
            continue
        n += 1
        prompt = c["input"].get("prompt", "")
        sec = next((l for l in prompt.splitlines() if l.startswith(("Section:", "Scaffold:"))), "")
        sub = subs.get(c["id"], {})
        rows.append(f"| {n} | {c['input'].get('subagent_type', '')} | {sec} | "
                    f"{first_line(c.get('result') or '').replace('|', '/')} | "
                    f"{first_line(sub.get('last_text', '')).replace('|', '/') or '(no transcript found)'} |")
    (outputs / "returns.md").write_text("\n".join(rows) + "\n")

    # --- status-final, git, repo copy ---
    st = subprocess.run(["python3", f"{plugin_dir}/skills/status/scripts/status.py", pkg],
                        cwd=copy, capture_output=True, text=True)
    (outputs / "status-final.txt").write_text(st.stdout + st.stderr)
    (outputs / "git-log.txt").write_text(
        git(copy, "log", "--format=%H%n%B", "--stat", f"{runner['seed_sha']}..HEAD"))
    (outputs / "git-oneline.txt").write_text(git(copy, "log", "--format=%h %s"))
    (outputs / "git-status.txt").write_text(git(copy, "status", "--porcelain"))
    repo = outputs / "repo"
    repo.mkdir(exist_ok=True)
    for d in ("docs", "tests", "packages"):
        if (copy / d).exists():
            subprocess.run(["rsync", "-a", "--exclude", ".git", "--exclude", ".venv",
                            "--exclude", "__pycache__", f"{copy / d}", str(repo)], check=False)
    for d in ("gate", "stop"):
        if (copy / ".dev-team" / d).exists():
            (repo / ".dev-team").mkdir(exist_ok=True)
            subprocess.run(["rsync", "-a", f"{copy / '.dev-team' / d}", str(repo / ".dev-team")], check=False)

    # --- gates.md ---
    g = ["# Gate records", ""]
    hist = sorted((outputs / "gate-history").glob("*.txt")) if (outputs / "gate-history").exists() else []
    finals = sorted((copy / ".dev-team" / "gate").glob("*/*.txt"))
    for f in hist:
        header = first_line(f.read_text(errors="replace"))
        g.append(f"- history `{f.name}` — mtime {stamp(f.stat().st_mtime)} — `{header}`")
    for f in finals:
        header = first_line(f.read_text(errors="replace"))
        g.append(f"- final `.dev-team/gate/{f.parent.name}/{f.name}` — mtime {stamp(f.stat().st_mtime)} — `{header}`")
    if not hist and not finals:
        g.append("no gate record was written in the copy")
    g.append("")
    batches: dict[int, list[dict]] = {}
    for c in tools:
        if c["name"] in ("Agent", "Task") and c["input"].get("subagent_type") == "dev-team:implementer":
            prompt = c["input"].get("prompt", "")
            if any(l.startswith("Section:") for l in prompt.splitlines()):
                batches.setdefault(batch_of.get(c.get("message_id") or c["id"], 0), []).append(c)
    for b, impls in sorted(batches.items()):
        if len(impls) < 2:
            continue
        windows = []
        for c in impls:
            sec = next(l.split(":", 1)[1].strip() for l in c["input"]["prompt"].splitlines() if l.startswith("Section:"))
            pk, _, s = sec.partition("/")
            versions = [f for f in hist if f.name.startswith(f"{pk}-{s}-")]
            sub = subs.get(c["id"], {})
            stamps = [parse_ts(x) for x in sub.get("assistant_stamps", [])]
            for f in versions:
                m = f.stat().st_mtime
                try:
                    m = float(f.name.rsplit("-", 1)[1][:-4])
                except ValueError:
                    pass
                before = [x for x in stamps if x is not None and x <= m]
                if before:
                    windows.append((sec, max(before), m))
        g.append(f"## Batch {b}: {', '.join(next(l for l in c['input']['prompt'].splitlines() if l.startswith('Section:')) for c in impls)}")
        for sec, a, z in windows:
            g.append(f"- {sec}: gate window {stamp(a)} → {stamp(z)}")
        overlap = [(x, y) for i, x in enumerate(windows) for y in windows[i + 1:]
                   if x[0] != y[0] and x[1] < y[2] and y[1] < x[2]]
        if not windows:
            g.append("- F4: not observable — no gate-record version could be matched to a transcript")
        elif overlap:
            g.append("- F4: overlap observed — " + "; ".join(f"{x[0]} and {y[0]}" for x, y in overlap))
        else:
            g.append("- F4: no overlap")
        g.append("")
    (outputs / "gates.md").write_text("\n".join(g) + "\n")

    # --- cost.json ---
    cost = {
        "models_seen": sorted(models),
        "total_cost_usd": (result or {}).get("total_cost_usd"),
        "duration_ms": (result or {}).get("duration_ms"),
        "num_turns": (result or {}).get("num_turns"),
        "modelUsage": (result or {}).get("modelUsage"),
        "exit_code": runner.get("exit_code"),
        "wall_seconds": runner.get("wall_seconds"),
        "subagent_runs": len(subs),
    }
    mu = cost["modelUsage"] or {}
    cost["tokens"] = sum(int(v.get(k, 0) or 0) for v in mu.values()
                         for k in ("inputTokens", "outputTokens", "cacheReadInputTokens", "cacheCreationInputTokens"))
    (outputs / "cost.json").write_text(json.dumps(cost, indent=1) + "\n")

    # --- transcript.md ---
    tr = [f"# Transcript — run-package eval {runner['eval_id']} ({runner['config']})", "",
          f"- command: `{runner['command']}`",
          f"- session: `{session_id}`; models named by its assistant records: {', '.join(sorted(models)) or 'none'}",
          f"- plugin dir: `{plugin_dir}`; copy: `{copy}`; seed commit `{runner['seed_sha']}`",
          f"- exit code {runner.get('exit_code')}, {runner.get('wall_seconds')} s",
          "", "## The driver, in order", ""]
    for c in calls:
        if c["kind"] == "text":
            tr += ["**text:**", "", c["text"].rstrip(), ""]
            continue
        inp = c["input"]
        if c["name"] == "Bash":
            what = f"`{inp.get('command', '')}`"
        elif c["name"] in ("Read", "Write", "Edit"):
            what = f"`{inp.get('file_path', '')}`"
            if c["name"] == "Read" and (inp.get("offset") or inp.get("limit")):
                what += f" (offset {inp.get('offset')}, limit {inp.get('limit')})"
        elif c["name"] == "Glob":
            what = f"`{inp.get('pattern', '')}` in `{inp.get('path', '')}`"
        elif c["name"] in ("Agent", "Task"):
            what = f"`{inp.get('subagent_type', '')}` — {first_line(inp.get('prompt', ''))}"
        else:
            what = "`" + json.dumps(inp)[:300] + "`"
        tr.append(f"**{c['name']}** {what}")
        if c["name"] in ("Write", "Edit"):
            body = inp.get("content") if c["name"] == "Write" else inp.get("new_string")
            tr += ["", "```", (body or "").rstrip(), "```"]
        res = c.get("result")
        if res is not None:
            if c["name"] in ("Agent", "Task"):
                res = first_line(res) + "  (first line of the return)"
            elif len(res) > 6000:
                res = res[:6000] + f"\n… ({len(res) - 6000} more characters)"
            tr += ["", "```", res.rstrip(), "```"]
        tr.append("")
    tr += ["## Final message", "", final.rstrip(), "", "--- harness copies ---", "",
           "Written by post.py after the session, read-only from the copy: outputs/status-final.txt, "
           "git-log.txt, git-oneline.txt, git-status.txt, repo/, gates.md, returns.md, cost.json; "
           "outputs/gate-history/ by run.sh's watcher during the session.", ""]
    (run_dir / "transcript.md").write_text("\n".join(tr))
    print(json.dumps({"tokens": cost["tokens"], "duration_ms": cost["duration_ms"],
                      "cost_usd": cost["total_cost_usd"], "spawns": index}))
    return 0


if __name__ == "__main__":
    sys.exit(main())
