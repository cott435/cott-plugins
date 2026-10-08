#!/usr/bin/env python3
"""Rebuild what a plugin's workflow actually did from Claude Code's session transcripts.

A session is one `<session>.jsonl` under `~/.claude/projects/<project>/`, plus one
`<session>/subagents/agent-<id>.jsonl` (and `.meta.json`) per agent spawned in it, at any
depth. This script reads them and writes a trace an auditor can hold against the plugin's
own files: who ran, what each was sent, every tool call in order with its key input and
whether it failed, every hook that blocked, every commit, and what each agent handed back.

It judges nothing. The auditor does that; this is the evidence.

It lives in plugin-dev's `skills/run-flow/scripts/`, beside `flow.py`, which draws the chart
and the unit pages. `run-flow` and `audit-run` both run it from there.

Usage:
  trace.py find --plugin NAME [--limit N] [--all]
      Sessions that used NAME's skills or agents, newest first, each with the chat's title
      as the app shows it, its project, its git branch, its span and the commands it ran.
  trace.py select DIR [--units risk|all|new|seg:N|U01,U05] [--cap N]
      Which units to audit, one per line with the reason, from DIR/index.json. `risk`
      (the default) is the first unit of each type plus every unit that stands out; `new`
      is every finished unit with no DIR/findings/U<nn>.md yet.
  trace.py flow DIR
      Re-render DIR/flow.html from DIR/index.json, adding a badge for every unit that has a
      findings file. `build` renders it too, before any audit.
  trace.py build SESSION --plugin NAME --out DIR [--full]
      SESSION is a .jsonl path, a session id (or unique prefix), `latest`, or words from
      the chat's title (case-insensitive, must match one session that used NAME).
      Writes DIR/run.md, DIR/index.json, DIR/driver/seg-<n>.md, DIR/units/U<nn>.md and
      DIR/units/U<nn>.system.md (the system prompt the agent actually ran with),
      DIR/units/U<nn>.json (every step with its full input and output, for the pages and
      the narrator; the `.md` stays clipped for auditors), and DIR/flow.html, the run as a
      chart, with DIR/units/U<nn>.html, one page per unit (see flow.py).
      --full raises every truncation limit fivefold.
  trace.py view --plugin NAME --agent TYPE --root DIR (--sessions a,b | --branch GLOB)
      Every run of one agent type across several sessions. Each session is built (or
      rebuilt) into DIR/<id8>/ as `build` would, then DIR/views/<type>-<YYYY-MM-DD>.html lists
      every unit of TYPE in time order, each linking to its unit page. TYPE matches a unit's
      role (`profiler`) or its full type (`dev-team:profiler`), ignoring case. --sessions takes
      ids, prefixes or paths; --branch takes every session of NAME, headless ones included,
      whose git branch matches GLOB.

Step ids are stable across rebuilds of the same transcript: `D<n>` in the main thread,
`U<nn>.S<n>` inside a unit. Units are numbered by first timestamp. A rebuild while the
session is still running appends new units and steps without renumbering old ones.
"""

from __future__ import annotations

import argparse
import datetime as dt
import fnmatch
import json
import os
import re
import subprocess
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))
import flow  # noqa: E402

PROJECTS = Path(os.environ.get("AUDIT_RUN_PROJECTS") or Path.home() / ".claude" / "projects")
LIMITS = {"text": 600, "cmd": 500, "err": 800, "out": 400, "arg": 200}

CMD_RE = re.compile(r"<command-name>/?([^<]+)</command-name>")
ARGS_RE = re.compile(r"<command-args>(.*?)</command-args>", re.S)
BASE_RE = re.compile(r"Base directory for this skill: (\S+)")
HANDBACK_RE = re.compile(r'<agent-message from="([^"]+)">')
TASK_RE = re.compile(r"<task-id>([^<]+)</task-id>.*?<status>([^<]*)</status>", re.S)
COMMIT_RE = re.compile(r"^\[([^\s\]]+)(?: \(root-commit\))? ([0-9a-f]{7,40})\] (.*)$", re.M)
ONELINE_RE = re.compile(r"^([0-9a-f]{7,40}) (.+)$", re.M)


def clip(s: str, kind: str) -> str:
    s = (s or "").strip()
    n = LIMITS[kind]
    return s if len(s) <= n else s[:n] + f" …[+{len(s) - n} chars]"


def tail(s: str, kind: str) -> str:
    s = (s or "").strip()
    n = LIMITS[kind]
    return s if len(s) <= n else f"…[{len(s) - n} chars] " + s[-n:]


def one_line(s: str) -> str:
    return " ⏎ ".join(x for x in (s or "").strip().splitlines() if x.strip())


def load(path: Path) -> list[dict]:
    out = []
    for line in path.open(encoding="utf-8", errors="replace"):
        line = line.strip()
        if line:
            try:
                out.append(json.loads(line))
            except json.JSONDecodeError:
                pass
    return out


def result_text(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


# ---------------------------------------------------------------- session discovery


TS_RE = re.compile(r'"timestamp":\s*"(\d{4}-\d\d-\d\dT[^"]+)"')


def title_of(text: str) -> str:
    """The chat's name as the app shows it: the last title set by hand or by the app, else the
    last title Claude generated, else the first thing typed."""
    for key in ("customTitle", "aiTitle"):
        hits = re.findall(rf'"{key}":\s*"((?:[^"\\]|\\.)*)"', text)
        if hits:
            return json.loads(f'"{hits[-1]}"')
    m = re.search(r'"lastPrompt":\s*"((?:[^"\\]|\\.)*)"', text)
    return json.loads(f'"{m.group(1)}"')[:60] if m else "(untitled)"


def local(ts: str) -> dt.datetime | None:
    try:
        return dt.datetime.fromisoformat(ts.replace("Z", "+00:00")).astimezone()
    except ValueError:
        return None


def describe(s: dict) -> str:
    """Two lines per session: id and title, then where, when, how long, how big."""
    start, end = local(s["first_ts"]), local(s["last_ts"])
    if start and end:
        mins = int((end - start).total_seconds() // 60)
        same_day = start.date() == end.date()
        span = (f"{start:%Y-%m-%d %H:%M} → {end:%H:%M}" if same_day else f"{start:%Y-%m-%d %H:%M} → {end:%m-%d %H:%M}")
        span += f" ({mins // 60}h{mins % 60:02d}m)"
    else:
        span = dt.datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
    live = " · still active" if dt.datetime.now().timestamp() - s["mtime"] < 120 else ""
    cmds = ", ".join(dict.fromkeys(c.split(":", 1)[1] for c in s["commands"])) or "—"
    where = s["cwd"].replace(str(Path.home()), "~") + (f" · {s['branch']}" if s.get("branch") else "")
    at = local(s.get("fork_at", ""))
    fork = (f"\n    fork of {s['fork_of'][:8]}: its history up to {at:%m-%d %H:%M} is a copy of that chat's"
            if s.get("fork_of") and at else "")
    return (f"{s['id']}  \"{s['title']}\"\n"
            f"    {where} · {span} · {s['spawns']} agent{'' if s['spawns'] == 1 else 's'} · commands: {cmds}{live}{fork}")


def headless(cwd: str) -> bool:
    """Eval harnesses run Claude headless in temp dirs; those runs never appear in the app."""
    return cwd.startswith(("/private/tmp/", "/tmp/", "/private/var/folders/", "/var/folders/"))


def sessions_for(plugin: str, include_headless: bool = False) -> list[dict]:
    needle_a, needle_b = f'"{plugin}:', f"/{plugin}:"
    found = []
    for f in PROJECTS.glob("*/*.jsonl"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if needle_a not in text and needle_b not in text:
            continue
        cmds, spawns, uuids = [], 0, []
        for line in text.splitlines():
            if '"uuid"' in line and (m := re.search(r'"uuid":\s*"([^"]+)"', line)):
                t = TS_RE.search(line)
                uuids.append((m.group(1), t.group(1) if t else ""))
            if f"/{plugin}:" not in line and "subagent_type" not in line:
                continue
            try:
                r = json.loads(line)
            except json.JSONDecodeError:
                continue
            content = (r.get("message") or {}).get("content")
            if r.get("type") == "user" and isinstance(content, str) and (m := CMD_RE.search(content)):
                if m.group(1).startswith(f"{plugin}:"):
                    cmds.append(m.group(1))  # typed, not quoted inside a tool's output
            elif r.get("type") == "assistant" and isinstance(content, list):
                spawns += sum(1 for b in content if isinstance(b, dict) and b.get("type") == "tool_use"
                              and b.get("name") in ("Agent", "Task")
                              and str((b.get("input") or {}).get("subagent_type", "")).startswith(f"{plugin}:"))
        cwd = re.search(r'"cwd":\s*"([^"]+)"', text)
        branch = re.search(r'"gitBranch":\s*"((?:[^"\\]|\\.)*)"', text)
        stamps = TS_RE.findall(text)
        found.append(
            {
                "path": f,
                "id": f.stem,
                "cwd": cwd.group(1) if cwd else "?",
                "branch": json.loads(f'"{branch.group(1)}"') if branch else None,
                "mtime": f.stat().st_mtime,
                "commands": cmds,
                "spawns": spawns,
                "title": title_of(text),
                "first_ts": min(stamps) if stamps else "",
                "last_ts": max(stamps) if stamps else "",
                "uuids": uuids,
                "born": getattr(f.stat(), "st_birthtime", f.stat().st_mtime),
                "own_agents": len(list((f.with_suffix("") / "subagents").glob("agent-*.jsonl"))),
            }
        )
    found = [s for s in found if (s["commands"] or s["spawns"]) and (include_headless or not headless(s["cwd"]))]
    mark_forks(found)
    return sorted(found, key=lambda s: -s["mtime"])


def mark_forks(sessions: list[dict]) -> None:
    """A fork or resumed copy shares its parent's record ids up to the point it split off.
    The older file of a pair is the parent (on a tie, the one holding more agent transcripts,
    which a fork leaves behind); the fork records where the two diverge."""
    by_project: dict[Path, list[dict]] = {}
    for s in sessions:
        by_project.setdefault(s["path"].parent, []).append(s)
    for group in by_project.values():
        for s in group:
            ids = [u for u, _ in s["uuids"]]
            for other in group:
                theirs = {u for u, _ in other["uuids"]}
                older = (other["born"], -other["own_agents"]) < (s["born"], -s["own_agents"])
                if other is s or not older or not ids or ids[0] not in theirs:
                    continue
                split = next((i for i, u in enumerate(ids) if u not in theirs), len(ids))
                s["fork_of"] = other["id"]
                s["fork_at"] = s["uuids"][split][1] if split < len(ids) else s["last_ts"]
                break


def resolve(session: str, plugin: str) -> Path:
    p = Path(session).expanduser()
    if p.suffix == ".jsonl" and p.exists():
        return p
    if session == "latest":
        hits = sessions_for(plugin)
        if not hits:
            sys.exit(f"no session under {PROJECTS} used {plugin}")
        return hits[0]["path"]
    hits = list(PROJECTS.glob(f"*/{session}*.jsonl")) if re.fullmatch(r"[\w-]{4,}", session) else []
    if len(hits) == 1:
        return hits[0]
    if len(hits) > 1:
        sys.exit(f"session id {session!r} matches {len(hits)} sessions; give more of it")
    words = session.lower().split()
    titled = [s for s in sessions_for(plugin) if all(w in s["title"].lower() for w in words)] or \
             [s for s in sessions_for(plugin, include_headless=True) if all(w in s["title"].lower() for w in words)]
    if len(titled) == 1:
        return titled[0]["path"]
    if not titled:
        sys.exit(f"no session id or {plugin} chat title matches {session!r}; run `find --plugin {plugin}`")
    more = f"\n… and {len(titled) - 8} older; add words from the title, or use the id" if len(titled) > 8 else ""
    sys.exit(f"{len(titled)} {plugin} chats match {session!r}; pick one by id:\n"
             + "\n".join(describe(s) for s in titled[:8]) + more)


# ---------------------------------------------------------------- one transcript → events


def summarize_call(name: str, inp: dict) -> str:
    if name == "Read":
        extra = "".join(f" {k}={inp[k]}" for k in ("offset", "limit") if k in inp)
        return f"{inp.get('file_path', '?')}{extra}"
    if name == "Write":
        body = inp.get("content", "")
        n = body.count("\n") + (0 if body.endswith("\n") or not body else 1)
        return f"{inp.get('file_path', '?')} ({n} lines)"
    if name == "Edit":
        old = one_line(inp.get("old_string", ""))[:80]
        new = one_line(inp.get("new_string", ""))[:80]
        flag = " replace_all" if inp.get("replace_all") else ""
        return f"{inp.get('file_path', '?')}{flag} | old: {old!r} | new: {new!r}"
    if name == "Bash":
        return clip(inp.get("command", ""), "cmd")
    if name in ("Grep", "Glob"):
        return f"{inp.get('pattern', '?')!r} in {inp.get('path', '.')}" + (
            f" glob={inp['glob']}" if inp.get("glob") else ""
        )
    if name == "Skill":
        return f"{inp.get('skill', '?')} {inp.get('args', '')}".strip()
    if name in ("Agent", "Task"):
        bg = " [background]" if inp.get("run_in_background") else ""
        return f"{inp.get('subagent_type', 'general-purpose')} — {inp.get('description', '')}{bg}"
    if name == "SubagentHandback":
        return clip(one_line(inp.get("message", "")), "text")
    if name == "AskUserQuestion":
        return " / ".join(q.get("question", "") for q in inp.get("questions", []))
    if name == "SendMessage":
        return f"to {inp.get('to', '?')}: {clip(one_line(inp.get('message', '')), 'arg')}"
    return clip(json.dumps(inp, ensure_ascii=False), "arg")


def events_of(records: list[dict]) -> tuple[list[dict], dict]:
    """Ordered events, plus facts about the transcript (system prompt, models, skill bases)."""
    events: list[dict] = []
    by_tool_id: dict[str, dict] = {}
    facts: dict = {"system": None, "models": set(), "bases": [], "cwd": None, "branch": None}

    def add(kind: str, rec: dict, **kw) -> dict:
        ev = {"kind": kind, "ts": rec.get("timestamp", ""), **kw}
        events.append(ev)
        return ev

    for rec in records:
        t = rec.get("type")
        facts["cwd"] = facts["cwd"] or rec.get("cwd")
        facts["branch"] = facts["branch"] or rec.get("gitBranch")
        msg = rec.get("message") or {}
        content = msg.get("content")

        if t == "assistant":
            if msg.get("model"):
                facts["models"].add(msg["model"])
            for b in content or []:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "text" and b.get("text", "").strip():
                    add("say", rec, text=b["text"])
                elif b.get("type") == "thinking" and b.get("thinking", "").strip():
                    add("think", rec, text=b["thinking"])
                elif b.get("type") == "tool_use":
                    ev = add("call", rec, id=b.get("id"), name=b.get("name"), input=b.get("input") or {},
                             mid=msg.get("id"))
                    by_tool_id[b.get("id")] = ev

        elif t == "user":
            blocks = content if isinstance(content, list) else [{"type": "text", "text": content or ""}]
            for b in blocks:
                if not isinstance(b, dict):
                    continue
                if b.get("type") == "tool_result":
                    ev = by_tool_id.get(b.get("tool_use_id"))
                    if ev is not None:
                        ev["error"] = bool(b.get("is_error"))
                        ev["result"] = result_text(b.get("content"))
                        tur = rec.get("toolUseResult")
                        if isinstance(tur, dict):
                            ev["meta"] = {
                                k: tur[k]
                                for k in ("agentId", "status", "totalDurationMs", "totalToolUseCount", "resolvedModel")
                                if k in tur
                            }
                    continue
                text = b.get("text", "") if b.get("type") == "text" else ""
                if not text.strip() or "<local-command-caveat>" in text:
                    continue
                if (m := BASE_RE.search(text)) and text.lstrip().startswith("Base directory"):
                    facts["bases"].append(m.group(1))
                    add("skill-body", rec, base=m.group(1))
                elif m := CMD_RE.search(text):
                    a = ARGS_RE.search(text)
                    add("command", rec, name=m.group(1), args=(a.group(1).strip() if a else ""))
                elif "<task-notification>" in text:
                    m = TASK_RE.search(text)
                    add("notify", rec, task=m.group(1) if m else "?", status=m.group(2) if m else "?", text=text)
                elif m := HANDBACK_RE.search(text):
                    add("handback", rec, frm=m.group(1))
                elif not rec.get("isMeta"):
                    add("user", rec, text=text)

        elif t == "attachment":
            att = rec.get("attachment") or {}
            at = att.get("type")
            if at == "prompt_snapshot":
                sp = att.get("systemPrompt")
                facts["system"] = "\n\n".join(sp) if isinstance(sp, list) else sp
            elif at == "hook_blocking_error":
                be = att.get("blockingError")
                text = be.get("blockingError") if isinstance(be, dict) else str(be)
                ev = add("hook", rec, hook=att.get("hookName"), block=True, text=text, tool=att.get("toolUseID"))
                if (call := by_tool_id.get(att.get("toolUseID"))) is not None:
                    call.setdefault("hooks", []).append(ev)
            elif at == "hook_success" and (att.get("stderr") or att.get("stdout") or "").strip():
                add("hook", rec, hook=att.get("hookName"), block=False,
                    text=(att.get("stderr") or "") + (att.get("stdout") or ""), tool=att.get("toolUseID"))
            elif at == "queued_command" and (m := HANDBACK_RE.search(att.get("prompt") or "")):
                add("handback", rec, frm=m.group(1))

        elif t == "system" and rec.get("subtype") in ("api_error",) or (t == "system" and rec.get("level") == "error"):
            err = rec.get("error") or {}
            add("system", rec, text=f"{rec.get('subtype')}: {err.get('formatted') or err.get('message') or ''}")

    for ev in events:  # skills injected before the agent's first turn were preloaded, not typed
        if ev["kind"] in ("say", "call", "think"):
            break
        if ev["kind"] == "command":
            ev["injected"] = True
    facts["models"] = sorted(facts["models"])
    return events, facts


def commits_of(ev: dict) -> list[str]:
    """Commits a Bash call that ran `git commit` made.

    `[branch sha] msg` in the output is certain. A `git log --oneline` line after a quiet
    commit is only HEAD after the call, and in a parallel run HEAD can be another agent's
    commit, so it is returned as `?sha` for the auditor to confirm with `git show`.
    """
    cmd = ev["input"].get("command", "") if ev.get("name") == "Bash" else ""
    if not re.search(r"\bgit\b[^|;&]*\bcommit\b", cmd):
        return []
    res = ev.get("result", "")
    sure = [m.group(2) for m in COMMIT_RE.finditer(res)]
    if sure:
        return sure
    if "git log" in cmd and (m := ONELINE_RE.search(res)):
        return [f"?{m.group(1)}"]
    return [] if ev.get("error") else ["?(sha not shown)"]


def confirm(shas: list[str], written: list[str], project: str | None) -> list[str]:
    """Drop the `?` from a HEAD-after SHA whose commit holds a file this unit wrote."""
    out = []
    for sha in shas:
        if not sha.startswith("?") or sha == "?(sha not shown)" or not project:
            out.append(sha)
            continue
        try:
            files = subprocess.run(["git", "-C", project, "show", "--name-only", "--format=", sha[1:]],
                                   capture_output=True, text=True, timeout=20).stdout.split()
        except (OSError, subprocess.TimeoutExpired):
            files = []
        mine = {str(Path(w).resolve().relative_to(Path(project).resolve())) for w in written
                if Path(w).is_absolute() and str(Path(w)).startswith(project)} | {w for w in written if not Path(w).is_absolute()}
        out.append(sha[1:] if mine & set(files) else sha)
    return out


# ---------------------------------------------------------------- full steps, for the pages


def commit_details(sha: str, ev: dict, project: str | None) -> dict:
    """One commit a call made: its message and files from the project when it still exists,
    else the message the call's own output printed and no files. Claims nothing else."""
    bare = sha.lstrip("?")
    out = {"sha": bare, "confirmed": not sha.startswith("?"), "message": "", "files": []}
    if sha == "?(sha not shown)":
        return out
    res = ev.get("result", "")
    for m in COMMIT_RE.finditer(res):
        if m.group(2) == bare:
            out["message"] = m.group(3).strip()
    if not out["message"] and (m := ONELINE_RE.search(res)) and m.group(1) == bare:
        out["message"] = m.group(2).strip()
    if project and Path(project).is_dir():
        try:
            shown = subprocess.run(["git", "-C", project, "show", "--name-only", "--format=%s", bare],
                                   capture_output=True, text=True, timeout=20)
        except (OSError, subprocess.TimeoutExpired):
            shown = None
        if shown is not None and shown.returncode == 0 and shown.stdout.strip():
            lines = shown.stdout.splitlines()
            out["message"] = lines[0].strip()
            out["files"] = [x.strip() for x in lines[1:] if x.strip()]
    return out


def full_step(ev: dict, hooks_by_call: dict, written: list[str], project: str | None) -> dict:
    """One numbered event, whole: nothing here is clipped."""
    k = ev["kind"]
    step = {"step": ev["step"], "kind": k, "ts": ev.get("ts", ""), "summary": ev.get("summary", "")}
    if k == "call":
        name, inp = ev["name"], ev["input"]
        step.update({
            "tool": name, "input": inp, "output": ev.get("result", ""), "error": bool(ev.get("error")),
            "hooks": [{"hook": h.get("hook"), "blocked": bool(h.get("block")), "text": h.get("text") or ""}
                      for h in hooks_by_call.get(ev.get("id"), [])],
            "commits": [commit_details(sha, ev, project) for sha in confirm(commits_of(ev), written, project)],
            "write": {"path": inp.get("file_path", ""), "content": inp.get("content", "")} if name == "Write" else None,
            "edit": ({"path": inp.get("file_path", ""), "old": inp.get("old_string", ""),
                      "new": inp.get("new_string", "")} if name == "Edit" else None),
        })
        if ev.get("meta"):
            step["meta"] = ev["meta"]
    elif k in ("say", "think", "user", "system"):
        step["text"] = ev.get("text", "")
    elif k == "command":
        step.update({"name": ev.get("name"), "args": ev.get("args", ""), "injected": bool(ev.get("injected"))})
    elif k == "skill-body":
        step["base"] = ev.get("base")
    elif k == "notify":
        step.update({"task": ev.get("task"), "status": ev.get("status"), "text": ev.get("text", "")})
    elif k == "handback":
        step["from"] = ev.get("frm")
    elif k == "hook":
        step.update({"hook": ev.get("hook"), "blocked": bool(ev.get("block")), "text": ev.get("text") or ""})
    return step


def unit_json(u: dict, iu: dict, project: str | None) -> dict:
    """`units/U<nn>.json`: the unit's every step with full input and output, numbered exactly as
    in `units/U<nn>.md`. A hook shown under its call there is in that call's `hooks` here."""
    hooks_by_call: dict[str, list[dict]] = {}
    for ev in u["events"]:
        if ev["kind"] == "hook" and ev.get("under_call"):
            hooks_by_call.setdefault(ev.get("tool"), []).append(ev)
    steps = [full_step(ev, hooks_by_call, iu["files_written"], project)
             for ev in u["events"] if not (ev["kind"] == "hook" and ev.get("under_call"))]
    return {
        "unit": iu["unit"], "agent_id": iu["agent_id"], "type": iu["type"], "description": iu["description"],
        "spawner": iu["spawner"], "spawn_step": iu.get("spawn_step"), "segment": iu.get("segment"),
        "background": iu["background"], "definition": iu["definition"], "version": iu["version"],
        "models": u["facts"]["models"], "first_ts": iu["first_ts"], "last_ts": iu["last_ts"],
        "finished": iu["finished"], "tool_calls": iu["tool_calls"], "errors": iu["errors"],
        "hook_blocks": iu["hook_blocks"],
        "skills": [e["input"].get("skill") for e in u["events"] if e["kind"] == "call" and e["name"] == "Skill"],
        "files_written": iu["files_written"], "commits": iu["commits"],
        "prompt": u["prompt"], "steps": steps, "return": u["return"], "step_count": len(steps),
    }


# ---------------------------------------------------------------- rendering


def render_call(ev: dict, units_by_agent: dict) -> list[str]:
    name = ev["name"]
    line = f"**{name}** {summarize_call(name, ev['input'])}"
    if name in ("Agent", "Task") and (aid := (ev.get("meta") or {}).get("agentId")):
        u = units_by_agent.get(aid)
        line += f" → **{u['unit']}**" if u else f" → agent {aid}"
    if ev.get("error"):
        line += "  ❌ ERROR"
    out = [line]
    res = ev.get("result", "")
    if ev.get("error"):
        out.append(f"    ↳ {clip(one_line(res), 'err')}")
    elif name == "Bash":
        for sha in commits_of(ev):
            out.append(f"    ↳ COMMIT {sha}" if not sha.startswith("?")
                       else f"    ↳ COMMIT UNCONFIRMED — HEAD after the call was {sha[1:]}; check `git show --stat {sha[1:]}`")
        if res.strip():
            out.append(f"    ↳ {tail(one_line(res), 'out')}")
    elif name in ("Agent", "Task"):
        meta = ev.get("meta") or {}
        if meta:
            out.append(
                f"    ↳ status={meta.get('status')} tools={meta.get('totalToolUseCount')} "
                f"ms={meta.get('totalDurationMs')} model={meta.get('resolvedModel')}"
            )
    elif name in ("Grep", "Glob"):
        out.append(f"    ↳ {clip(one_line(res), 'arg')}")
    elif name == "Read":
        out.append(f"    ↳ {res.count(chr(10)) + 1 if res else 0} lines")
    elif name == "AskUserQuestion":
        out.append(f"    ↳ {clip(one_line(res), 'err')}")
    for h in ev.get("hooks", []):
        out.append(f"    ⛔ HOOK {h['hook']} blocked: {clip(one_line(h['text']), 'err')}")
    return out


def render_events(events: list[dict], prefix: str, units_by_agent: dict, start: int = 1) -> list[str]:
    lines = []
    n = start - 1
    for ev in events:
        n += 1
        ev["step"] = f"{prefix}{n}"
        k = ev["kind"]
        head = f"- `{ev['step']}` "
        if k == "call":
            body = render_call(ev, units_by_agent)
            lines.append(head + body[0])
            lines.extend("  " + b for b in body[1:])
            ev["summary"] = body[0]
            continue
        elif k == "say":
            lines.append(head + f"_said:_ {clip(one_line(ev['text']), 'text')}")
        elif k == "think":
            lines.append(head + f"_thought:_ {clip(one_line(ev['text']), 'text')}")
        elif k == "command":
            if prefix != "D" and ev.get("injected"):
                lines.append(head + f"skill preloaded: `{ev['name']}`")
            else:
                lines.append(head + f"**USER TYPED** `/{ev['name']} {ev['args']}`".rstrip())
        elif k == "user":
            lines.append(head + f"**USER:** {clip(one_line(ev['text']), 'text')}")
        elif k == "skill-body":
            lines.append(head + f"skill loaded from `{ev['base']}`")
        elif k == "notify":
            u = units_by_agent.get(ev["task"])
            who = u["unit"] if u else ev["task"]
            lines.append(head + f"← background task {who} {ev['status']}")
        elif k == "handback":
            u = units_by_agent.get(ev["frm"])
            who = u["unit"] if u else ev["frm"]
            first = one_line(u["return"]).split(" ⏎ ")[0] if u and u.get("return") else ""
            lines.append(head + f"← **{who} handed back:** {clip(first, 'arg')}")
        elif k == "hook":
            if ev.get("tool") and any(e.get("id") == ev["tool"] for e in events if e["kind"] == "call"):
                n -= 1  # shown under its call
                ev["under_call"] = True
                continue
            verb = "blocked" if ev["block"] else "said"
            lines.append(head + f"⛔ HOOK {ev['hook']} {verb}: {clip(one_line(ev['text']), 'err')}")
        elif k == "system":
            lines.append(head + f"⚠ {ev['text']}")
        ev["summary"] = lines[-1][len(head):]
    return lines


SECTION_RE = re.compile(r"^Section:\s*(\S+)", re.M)
PATHLIKE_RE = re.compile(r"\b([a-z][\w-]*/[a-z][\w.-]*[\w])\b")


def lane_of(prompt: str, description: str) -> str | None:
    """What a unit worked on: a `Section:` input, else the first `a/b` name in its description or prompt."""
    if m := SECTION_RE.search(prompt or ""):
        return m.group(1)
    for text in (description, prompt):
        if m := PATHLIKE_RE.search(text or ""):
            return m.group(1)
    return None


MODE_RE = re.compile(r"^Mode:\s*(.+)$", re.M)


def mode_of(prompt: str) -> str | None:
    """The prompt's first `Mode:` line, when it has one."""
    m = MODE_RE.search(prompt or "")
    return m.group(1).strip() if m else None


def outcome(ret: str, description: str) -> dict:
    """The `Result:` of a return and, for a review, its verdict, counts and round. Heuristic, by design."""
    first = one_line(ret).split(" ⏎ ")[0] if ret else ""
    res = re.match(r"\W*Result:\W*([\w-]+)", first)
    out: dict = {"result": res.group(1).lower() if res else None, "verdict": None,
                 "critical": None, "warning": None, "round": None}
    v = re.search(r"Verdict:\W*(approve|request changes|spec-change|reject|blocked|defer)", ret or "", re.I)
    if v:
        out["verdict"] = v.group(1).lower()
        # "round-1 CRITICAL" is not a count: a count is a bare number, preferably beside its warnings
        both = re.search(r"(?<![\w-])(\d+)\s+critical\b[^.\n]{0,20}?(?<![\w-])(\d+)\s+warnings?", ret, re.I)
        crit = both or re.search(r"(?<![\w-])(\d+)\s+critical", ret, re.I)
        warn = re.search(r"(?<![\w-])(\d+)\s+warnings?", ret, re.I)
        out["critical"] = int(crit.group(1)) if crit else None
        out["warning"] = int(both.group(2)) if both else int(warn.group(1)) if warn else None
    if out["result"] in ("blocked", "stopped"):  # it wrote no review, whatever its text says it would have
        out["verdict"] = out["result"]
    if m := re.search(r"\bRound:?\W*(\d+)", ret or "") or re.search(r"\br(\d+)\b", description or ""):
        out["round"] = int(m.group(1))
    return out


def unit_return(events: list[dict]) -> str:
    for ev in reversed(events):
        if ev["kind"] == "call" and ev["name"] == "SubagentHandback":
            return ev["input"].get("message", "")
    for ev in reversed(events):
        if ev["kind"] == "say":
            return ev["text"]
    return ""


# ---------------------------------------------------------------- plugin root


def plugin_root(bases: list[str], plugin: str) -> tuple[str | None, str | None]:
    counts: dict[str, int] = {}
    for b in bases:
        p = Path(b)
        root = p.parent.parent if p.parent.name == "skills" else None
        if root is None or f"/{plugin}/" not in f"{root}/":
            continue
        counts[str(root)] = counts.get(str(root), 0) + 1
    if not counts:
        return None, None
    root = max(counts, key=counts.get)
    manifest = Path(root) / ".claude-plugin" / "plugin.json"
    version = None
    if manifest.exists():
        try:
            version = json.loads(manifest.read_text()).get("version")
        except json.JSONDecodeError:
            pass
    if version is None:
        parts = Path(root).parts
        if plugin in parts and parts.index(plugin) + 1 < len(parts):
            version = parts[parts.index(plugin) + 1]
    return root, version


def definition_for(agent_type: str, first_base: str | None, plugin: str, root: str | None) -> str | None:
    if first_base:
        return str(Path(first_base) / "SKILL.md")
    if root and agent_type.startswith(f"{plugin}:"):
        return str(Path(root) / "agents" / f"{agent_type.split(':', 1)[1]}.md")
    return None


# ---------------------------------------------------------------- build


def agent_files(session_path: Path, main_events: list[dict]) -> list[Path]:
    """Every spawned agent's transcript: the session's own, plus any a fork left behind.

    A forked or resumed chat copies its parent's history into a new session file, but the
    transcripts of agents spawned before the fork stay under the parent's directory. Those
    are found in the project's other sessions by the spawning call's tool_use id, which the
    copy keeps; nested spawns are followed until nothing new turns up.
    """
    own = sorted((session_path.with_suffix("") / "subagents").glob("agent-*.jsonl"))
    wanted = {e["id"] for e in main_events if e["kind"] == "call" and e["name"] in ("Agent", "Task")}
    have = {f.stem for f in own}
    for f in own:
        wanted |= set(re.findall(r'"type":\s*"tool_use",\s*"id":\s*"([^"]+)",\s*"name":\s*"(?:Agent|Task)"',
                                 f.read_text(encoding="utf-8", errors="replace")))
    elsewhere = [m for m in session_path.parent.glob("*/subagents/agent-*.meta.json")
                 if m.parent.parent != session_path.with_suffix("")]
    found = list(own)
    grew = True
    while grew:
        grew = False
        for m in elsewhere:
            f = m.with_name(m.name.removesuffix(".meta.json") + ".jsonl")
            if f.stem in have or not f.exists():
                continue
            try:
                tid = json.loads(m.read_text()).get("toolUseId")
            except (OSError, json.JSONDecodeError):
                continue
            if tid in wanted:
                found.append(f)
                have.add(f.stem)
                wanted |= set(re.findall(r'"id":\s*"([^"]+)",\s*"name":\s*"(?:Agent|Task)"',
                                         f.read_text(encoding="utf-8", errors="replace")))
                grew = True
    return found


def build(session_path: Path, plugin: str, out: Path, quiet: bool = False) -> dict:
    main_records = load(session_path)
    main_events, main_facts = events_of(main_records)
    raw_units = []
    for f in agent_files(session_path, main_events):
        aid = f.stem.removeprefix("agent-")
        meta_p = f.with_suffix(".meta.json")
        meta = json.loads(meta_p.read_text()) if meta_p.exists() else {}
        recs = load(f)
        evs, facts = events_of(recs)
        first_ts = next((r.get("timestamp") for r in recs if r.get("timestamp")), "")
        raw_units.append({"agent": aid, "meta": meta, "events": evs, "facts": facts, "ts": first_ts, "records": recs})
    raw_units.sort(key=lambda u: (u["ts"], u["agent"]))

    all_bases = list(main_facts["bases"]) + [b for u in raw_units for b in u["facts"]["bases"]]
    root, version = plugin_root(all_bases, plugin)

    # Which tool_use spawned which agent: the parent Agent call's id is meta.toolUseId.
    spawn_site: dict[str, tuple[str, dict]] = {}
    for ev in main_events:
        if ev["kind"] == "call":
            spawn_site[ev["id"]] = ("driver", ev)
    units_by_agent: dict[str, dict] = {}
    for i, u in enumerate(raw_units, 1):
        u["unit"] = f"U{i:02d}"
        units_by_agent[u["agent"]] = u
        for ev in u["events"]:
            if ev["kind"] == "call":
                spawn_site[ev["id"]] = (u["unit"], ev)

    for u in raw_units:
        meta = u["meta"]
        site = spawn_site.get(meta.get("toolUseId", ""))
        u["spawner"] = site[0] if site else "?"
        u["spawn_call"] = site[1] if site else None
        u["type"] = meta.get("agentType") or (site[1]["input"].get("subagent_type") if site else "?")
        u["description"] = meta.get("description") or (site[1]["input"].get("description", "") if site else "")
        u["background"] = bool(site and site[1]["input"].get("run_in_background")) or meta.get("requestShape") == "background"
        first_base = u["events"][0]["base"] if u["events"] and u["events"][0]["kind"] == "skill-body" else None
        u["forked_skill"] = first_base
        u_root, u["version"] = plugin_root(u["facts"]["bases"], plugin)
        u["root"] = u_root or root
        u["version"] = u["version"] or version
        u["definition"] = definition_for(u["type"], first_base, plugin, u["root"])
        u["return"] = unit_return(u["events"])
        u["prompt"] = (site[1]["input"].get("prompt", "") if site else "") or next(
            (r["message"]["content"] for r in u["records"] if r.get("type") == "user"
             and isinstance((r.get("message") or {}).get("content"), str)), "")

    # Render units first so step ids exist; the driver refers to units by id.
    (out / "units").mkdir(parents=True, exist_ok=True)
    (out / "driver").mkdir(parents=True, exist_ok=True)
    index_units = []
    for u in raw_units:
        steps = render_events(u["events"], f"{u['unit']}.S", units_by_agent)
        calls = [e for e in u["events"] if e["kind"] == "call"]
        written = sorted({e["input"].get("file_path") for e in calls if e["name"] in ("Write", "Edit", "NotebookEdit") and e["input"].get("file_path")})
        skills = [e["input"].get("skill") for e in calls if e["name"] == "Skill"]
        commits = confirm([sha for e in calls for sha in commits_of(e)], written, main_facts["cwd"])
        errors = sum(1 for e in calls if e.get("error"))
        blocks = sum(1 for e in u["events"] if e["kind"] == "hook" and e["block"])
        spawned_at = u["spawn_call"]["step"] if u["spawn_call"] and "step" in u["spawn_call"] else None
        doc = [
            f"# {u['unit']} · {u['type']} · {u['description']}",
            "",
            f"- **Agent id:** `{u['agent']}` · **spawned by:** {u['spawner']} · "
            f"**mode:** {'background' if u['background'] else 'foreground'} · **depth:** {u['meta'].get('spawnDepth', '?')}",
            f"- **Definition:** `{u['definition'] or 'none (not a plugin agent)'}`"
            + (f" (forked skill)" if u["forked_skill"] else ""),
            f"- **System prompt as run:** `units/{u['unit']}.system.md`" if u["facts"]["system"] else "- **System prompt as run:** not recorded",
            f"- **Model:** {', '.join(u['facts']['models']) or '?'} · **first/last:** {u['ts']} / {u['events'][-1]['ts'] if u['events'] else '?'}",
            f"- **Tool calls:** {len(calls)} · **errors:** {errors} · **hook blocks:** {blocks} · "
            f"**skills invoked:** {', '.join(skills) or 'none'} · **commits:** {', '.join(commits) or 'none'}",
            f"- **Files written:** {', '.join(f'`{w}`' for w in written) or 'none'}",
            "",
            "## Prompt it was sent",
            "",
            "```text",
            u["prompt"].strip(),
            "```",
            "",
            "## Steps",
            "",
            *steps,
            "",
            "## What it handed back",
            "",
            "```text",
            u["return"].strip() or "(nothing)",
            "```",
            "",
        ]
        (out / "units" / f"{u['unit']}.md").write_text("\n".join(doc), encoding="utf-8")
        if u["facts"]["system"]:
            (out / "units" / f"{u['unit']}.system.md").write_text(u["facts"]["system"], encoding="utf-8")
        index_units.append({
            "unit": u["unit"], "agent_id": u["agent"], "type": u["type"], "description": u["description"],
            "spawner": u["spawner"], "background": u["background"], "definition": u["definition"], "version": u["version"],
            "forked_skill": bool(u["forked_skill"]), "trace": f"units/{u['unit']}.md",
            "json": f"units/{u['unit']}.json",
            "tool_calls": len(calls), "errors": errors, "hook_blocks": blocks, "commits": commits,
            "files_written": written, "first_ts": u["ts"],
            "last_ts": u["events"][-1]["ts"] if u["events"] else "",
            "finished": any(e["kind"] == "call" and e["name"] == "SubagentHandback" for e in u["events"])
                        or bool(u["spawn_call"] and "result" in u["spawn_call"]),
            "return_first_line": one_line(u["return"]).split(" ⏎ ")[0][:200] if u["return"] else "",
            "wave_key": f"{u['spawner']}:{(u['spawn_call'] or {}).get('mid') or u['agent']}",
            "lane": lane_of(u["prompt"], u["description"]),
            "role": u["type"].split(":")[-1],
            "mode": mode_of(u["prompt"]),
            **outcome(u["return"], u["description"]),
        })

    # Driver: the main thread, split into segments at each command of this plugin.
    driver_lines = render_events(main_events, "D", units_by_agent)
    for u in raw_units:
        if u["spawn_call"] is not None and "step" in u["spawn_call"]:
            for iu in index_units:
                if iu["unit"] == u["unit"]:
                    iu["spawn_step"] = u["spawn_call"]["step"]
    segments = []
    cur = None
    for ev, line_idx in zip(main_events, range(len(main_events))):
        if ev["kind"] == "command" and ev["name"].startswith(f"{plugin}:"):
            cur = {"seg": len(segments) + 1, "command": f"/{ev['name']} {ev['args']}".strip(),
                   "skill": ev["name"].split(":", 1)[1], "first": ev.get("step"), "events": []}
            segments.append(cur)
        if cur is not None:
            cur["events"].append(ev)
    index_segments = []
    for s in segments:
        steps = [e.get("step") for e in s["events"] if e.get("step")]
        s["last"] = steps[-1] if steps else s["first"]
        body = render_events(s["events"], "D", units_by_agent,
                             start=int(s["first"][1:]) if s["first"] else 1)
        spawned = [u["unit"] for u in raw_units if u["spawner"] == "driver"
                   and u["spawn_call"] is not None and u["spawn_call"] in s["events"]]
        s_root, s_version = plugin_root([e["base"] for e in s["events"] if e["kind"] == "skill-body"], plugin)
        s_root, s_version = s_root or root, s_version or version
        definition = str(Path(s_root) / "skills" / s["skill"] / "SKILL.md") if s_root else None
        doc = [
            f"# Driver segment {s['seg']} · `{s['command']}`",
            "",
            f"- **Steps:** {s['first']}–{s['last']} · **definition:** `{definition}`",
            f"- **Units spawned here:** {', '.join(spawned) or 'none'}",
            "",
            "## Steps",
            "",
            *body,
            "",
        ]
        (out / "driver" / f"seg-{s['seg']}.md").write_text("\n".join(doc), encoding="utf-8")
        index_segments.append({"seg": s["seg"], "command": s["command"], "definition": definition,
                               "plugin_root": s_root, "version": s_version,
                               "trace": f"driver/seg-{s['seg']}.md", "first": s["first"], "last": s["last"],
                               "units": spawned})

    # Units spawned below the driver belong to their top-level ancestor's segment.
    seg_of = {u: s["seg"] for s in index_segments for u in s["units"]}
    changed = True
    while changed:
        changed = False
        for iu in index_units:
            if iu["unit"] not in seg_of and iu["spawner"] in seg_of:
                seg_of[iu["unit"]] = seg_of[iu["spawner"]]
                changed = True
    for iu in index_units:
        iu["segment"] = seg_of.get(iu["unit"])

    # Full steps, one JSON per unit: written last, once spawn steps and segments are known.
    for u, iu in zip(raw_units, index_units):
        doc = unit_json(u, iu, main_facts["cwd"])
        iu["step_count"] = doc["step_count"]
        (out / "units" / f"{u['unit']}.json").write_text(json.dumps(doc, indent=2, ensure_ascii=False),
                                                         encoding="utf-8")

    interventions = []
    for ev in main_events:
        if ev["kind"] == "call" and ev["name"] == "AskUserQuestion":
            interventions.append({"step": ev.get("step"), "ts": ev["ts"], "kind": "asked",
                                  "text": summarize_call("AskUserQuestion", ev["input"]),
                                  "answer": "; ".join(re.findall(r'"="(.*?)"(?=[.,;]|\s|$)', ev.get("result", "")))
                                            or one_line(ev.get("result", ""))[:300]})
        elif ev["kind"] == "user":
            interventions.append({"step": ev.get("step"), "ts": ev["ts"], "kind": "said",
                                  "text": one_line(ev["text"])[:300], "answer": ""})

    index = {
        "session": session_path.stem, "transcript": str(session_path), "plugin": plugin,
        "title": title_of(session_path.read_text(encoding="utf-8", errors="replace")),
        "plugin_root": root, "plugin_root_exists": bool(root and Path(root).exists()), "version": version,
        "project": main_facts["cwd"], "branch": main_facts["branch"],
        "models": sorted(set(main_facts["models"]) | {m for u in raw_units for m in u["facts"]["models"]}),
        "first_ts": main_events[0]["ts"] if main_events else "", "last_ts": main_events[-1]["ts"] if main_events else "",
        "segments": index_segments, "units": index_units, "interventions": interventions,
    }
    (out / "index.json").write_text(json.dumps(index, indent=2), encoding="utf-8")

    run = [
        f"# Run trace · {plugin} · session `{session_path.stem}`",
        "",
        f"- **Project:** `{index['project']}` · **branch:** `{index['branch']}`",
        f"- **Plugin that ran:** `{root}` · version **{version}**"
        + ("" if index["plugin_root_exists"] else " · ⚠ that directory no longer exists"),
        f"- **Models:** {', '.join(index['models']) or '?'} · **span:** {index['first_ts']} → {index['last_ts']}",
        "",
        "## Segments",
        "",
        "| Seg | Command | Steps | Units |",
        "|---|---|---|---|",
        *[f"| {s['seg']} | `{s['command']}` | {s['first']}–{s['last']} | {', '.join(s['units']) or '—'} |" for s in index_segments],
        "",
        "## Units",
        "",
        "| Unit | Seg | Type | Description | By | Tools | Err | Hook blocks | Commits | Returned |",
        "|---|---|---|---|---|---|---|---|---|---|",
        *[f"| {u['unit']} | {u['segment'] or '—'} | {u['type']} | {u['description']} | {u['spawner']}"
          f"{' ' + u['spawn_step'] if u.get('spawn_step') else ''} | {u['tool_calls']} | {u['errors']} | "
          f"{u['hook_blocks']} | {', '.join(u['commits']) or '—'} | {u['return_first_line'][:90] or '(running or none)'} |"
          for u in index_units],
        "",
        "## Driver (whole main thread)",
        "",
        *driver_lines,
        "",
    ]
    run[run.index("## Driver (whole main thread)"):run.index("## Driver (whole main thread)")] = flow.text(index) + [""]
    (out / "run.md").write_text("\n".join(run), encoding="utf-8")
    flow.write_html(out)
    if quiet:
        return index
    print(f"trace: {out}  (flow chart: {out / 'flow.html'})")
    print(f"  plugin root: {root} (version {version}){'' if index['plugin_root_exists'] else ' — MISSING on disk'}")
    print(f"  segments: {len(index_segments)} · units: {len(index_units)} · driver steps: {len(main_events)}")
    for s in index_segments:
        print(f"  seg {s['seg']}: {s['command']} — {len(s['units'])} units spawned directly · {plugin} {s['version']}")
    versions = sorted({s["version"] for s in index_segments} | {u["version"] for u in raw_units} - {None})
    if len(versions) > 1:
        print(f"  ⚠ the run spans {plugin} versions {', '.join(versions)}: each segment's and unit's "
              f"definition in index.json points at the version it ran")
    return index


def view(plugin: str, agent: str, root: Path, sessions: str | None, branch: str | None) -> int:
    """Build each session into root/<id8>/, then the cross-session page for one agent type."""
    if sessions:
        paths = [resolve(x.strip(), plugin) for x in sessions.split(",") if x.strip()]
    else:
        paths = [s["path"] for s in sessions_for(plugin, include_headless=True)
                 if s["branch"] is not None and fnmatch.fnmatchcase(s["branch"], branch)]
        if not paths:
            print(f"no session of {plugin} on a branch matching {branch}")
            return 1
    paths = list(dict.fromkeys(paths))
    workspaces, lines = [], []
    for path in paths:
        out = root / path.stem[:8]
        index = build(path, plugin, out, quiet=True)
        workspaces.append(out)
        n = sum(1 for u in index["units"] if flow.is_type(u, agent))
        lines.append(f"{path.stem[:8]} · {index['title']} · {index['branch'] or '—'} · {n} unit{'' if n == 1 else 's'} of {agent}")
    page = flow.write_view(root, workspaces, agent, dt.date.today().isoformat())
    print(page)
    for line in lines:
        print(line)
    return 0


def shape(first_line: str) -> str:
    m = re.match(r"^\W*([A-Z][\w -]{0,24}):\W*(\w+)", first_line)
    return f"{m.group(1)}: {m.group(2)}" if m else "(free text)"


def select(out: Path, how: str, cap: int) -> list[tuple[str, str]]:
    index = json.loads((out / "index.json").read_text())
    units = index["units"]
    done = [u for u in units if u["finished"]]
    if how == "all":
        return [(u["unit"], "all") for u in done]
    if how == "new":
        return [(u["unit"], "new") for u in done if not (out / "findings" / f"{u['unit']}.md").exists()]
    if how.startswith("seg:"):
        seg = int(how[4:])
        return [(u["unit"], f"segment {seg}") for u in done if u["segment"] == seg]
    if how != "risk":
        wanted = [x.strip() for x in how.split(",") if x.strip()]
        return [(w, "named") for w in wanted]

    # risk: what stands out against units of the same type
    by_type: dict[str, list[dict]] = {}
    for u in done:
        by_type.setdefault(u["type"], []).append(u)
    scored: dict[str, tuple[int, list[str]]] = {}

    def mark(u: dict, pts: int, why: str) -> None:
        s, r = scored.get(u["unit"], (0, []))
        scored[u["unit"]] = (s + pts, r + [why])

    for t, us in by_type.items():
        mark(us[0], 1, f"first {t}")
        firsts = [shape(u["return_first_line"]) for u in us]
        common = max(set(firsts), key=firsts.count)
        committing = sum(1 for u in us if u["commits"]) > len(us) / 2
        for u, first in zip(us, firsts):
            if len(us) > 1 and first != common:
                mark(u, 3, f"returned {first!r} where most {t} returned {common!r}")
            if committing and not [c for c in u["commits"] if not c.startswith("?(")]:
                mark(u, 2, f"no commit where most {t} committed")
            if any(c.startswith("?") and c != "?(sha not shown)" for c in u["commits"]):
                mark(u, 2, "commit unconfirmed")
            if u["hook_blocks"] >= 3:
                mark(u, 2, f"{u['hook_blocks']} hook blocks")
            if u["errors"] >= 4:
                mark(u, 1, f"{u['errors']} tool errors")
            if u["spawner"] != "driver":
                mark(u, 1, f"spawned by {u['spawner']}")
    ranked = sorted(scored.items(), key=lambda kv: (-kv[1][0], kv[0]))[:cap]
    return sorted(((k, "; ".join(v[1])) for k, v in ranked), key=lambda x: x[0])


def main() -> int:
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    sub = ap.add_subparsers(dest="cmd", required=True)
    f = sub.add_parser("find")
    f.add_argument("--plugin", required=True)
    f.add_argument("--limit", type=int, default=8)
    f.add_argument("--all", action="store_true", help="include headless runs in temp dirs (eval harnesses)")
    fl = sub.add_parser("flow")
    fl.add_argument("out")
    se = sub.add_parser("select")
    se.add_argument("out")
    se.add_argument("--units", default="risk")
    se.add_argument("--cap", type=int, default=12)
    b = sub.add_parser("build")
    b.add_argument("session")
    b.add_argument("--plugin", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--full", action="store_true")
    v = sub.add_parser("view")
    v.add_argument("--plugin", required=True)
    v.add_argument("--agent", required=True)
    v.add_argument("--root", required=True)
    which = v.add_mutually_exclusive_group(required=True)
    which.add_argument("--sessions")
    which.add_argument("--branch")
    a = ap.parse_args()

    if a.cmd == "find":
        hits = sessions_for(a.plugin, include_headless=a.all)[: a.limit]
        if not hits:
            print(f"no session under {PROJECTS} used {a.plugin}")
            return 1
        for s in hits:
            print(describe(s))
        return 0

    if a.cmd == "flow":
        print(flow.write_html(Path(a.out)))
        return 0

    if a.cmd == "select":
        index = json.loads((Path(a.out) / "index.json").read_text())
        running = [u["unit"] for u in index["units"] if not u["finished"]]
        picked = select(Path(a.out), a.units, a.cap)
        for unit, why in picked:
            print(f"{unit}  {why}")
        print(f"selected {len(picked)} of {len(index['units'])} units"
              + (f"; still running, never selected: {', '.join(running)}" if running else ""))
        return 0

    if a.cmd == "view":
        return view(a.plugin, a.agent, Path(a.root), a.sessions, a.branch)

    if a.full:
        for k in LIMITS:
            LIMITS[k] *= 5
    build(resolve(a.session, a.plugin), a.plugin, Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
