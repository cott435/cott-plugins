#!/usr/bin/env python3
"""Rebuild what a plugin's workflow actually did from Claude Code's session transcripts.

A session is one `<session>.jsonl` under `~/.claude/projects/<project>/`, plus one
`<session>/subagents/agent-<id>.jsonl` (and `.meta.json`) per agent spawned in it, at any
depth. This script reads them and writes a trace an auditor can hold against the plugin's
own files: who ran, what each was sent, every tool call in order with its key input and
whether it failed, every hook that blocked, every commit, and what each agent handed back.

It judges nothing. The auditor does that; this is the evidence.

Usage:
  trace.py find --plugin NAME [--limit N]
      Sessions that used NAME's skills or agents, newest first.
  trace.py select DIR [--units risk|all|new|seg:N|U01,U05] [--cap N]
      Which units to audit, one per line with the reason, from DIR/index.json. `risk`
      (the default) is the first unit of each type plus every unit that stands out; `new`
      is every finished unit with no DIR/findings/U<nn>.md yet.
  trace.py build SESSION --plugin NAME --out DIR [--full]
      SESSION is a .jsonl path, a session id (or unique prefix), or `latest`.
      Writes DIR/run.md, DIR/index.json, DIR/driver/seg-<n>.md, DIR/units/U<nn>.md and
      DIR/units/U<nn>.system.md (the system prompt the agent actually ran with).
      --full raises every truncation limit fivefold.

Step ids are stable across rebuilds of the same transcript: `D<n>` in the main thread,
`U<nn>.S<n>` inside a unit. Units are numbered by first timestamp. A rebuild while the
session is still running appends new units and steps without renumbering old ones.
"""

from __future__ import annotations

import argparse
import json
import re
import subprocess
import sys
from pathlib import Path

PROJECTS = Path.home() / ".claude" / "projects"
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


def sessions_for(plugin: str) -> list[dict]:
    needle_a, needle_b = f'"{plugin}:', f"/{plugin}:"
    found = []
    for f in PROJECTS.glob("*/*.jsonl"):
        try:
            text = f.read_text(encoding="utf-8", errors="replace")
        except OSError:
            continue
        if needle_a not in text and needle_b not in text:
            continue
        cmds = [
            m.group(1)
            for m in CMD_RE.finditer(text)
            if m.group(1).startswith(f"{plugin}:")
        ]
        spawns = len(re.findall(rf'"subagent_type":\s*"{re.escape(plugin)}:', text))
        cwd = re.search(r'"cwd":\s*"([^"]+)"', text)
        found.append(
            {
                "path": f,
                "id": f.stem,
                "cwd": cwd.group(1) if cwd else "?",
                "mtime": f.stat().st_mtime,
                "commands": cmds,
                "spawns": spawns,
            }
        )
    found = [s for s in found if s["commands"] or s["spawns"]]
    return sorted(found, key=lambda s: -s["mtime"])


def resolve(session: str, plugin: str) -> Path:
    p = Path(session).expanduser()
    if p.suffix == ".jsonl" and p.exists():
        return p
    if session == "latest":
        hits = sessions_for(plugin)
        if not hits:
            sys.exit(f"no session under {PROJECTS} used {plugin}")
        return hits[0]["path"]
    hits = list(PROJECTS.glob(f"*/{session}*.jsonl"))
    if len(hits) != 1:
        sys.exit(f"session {session!r}: {len(hits)} matches under {PROJECTS}")
    return hits[0]


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
                    ev = add("call", rec, id=b.get("id"), name=b.get("name"), input=b.get("input") or {})
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
                continue
            verb = "blocked" if ev["block"] else "said"
            lines.append(head + f"⛔ HOOK {ev['hook']} {verb}: {clip(one_line(ev['text']), 'err')}")
        elif k == "system":
            lines.append(head + f"⚠ {ev['text']}")
    return lines


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


def build(session_path: Path, plugin: str, out: Path) -> None:
    main_records = load(session_path)
    main_events, main_facts = events_of(main_records)
    sub_dir = session_path.with_suffix("") / "subagents"

    raw_units = []
    for f in sorted(sub_dir.glob("agent-*.jsonl")) if sub_dir.exists() else []:
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
        u["definition"] = definition_for(u["type"], first_base, plugin, root)
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
            "spawner": u["spawner"], "background": u["background"], "definition": u["definition"],
            "forked_skill": bool(u["forked_skill"]), "trace": f"units/{u['unit']}.md",
            "tool_calls": len(calls), "errors": errors, "hook_blocks": blocks, "commits": commits,
            "files_written": written, "first_ts": u["ts"],
            "last_ts": u["events"][-1]["ts"] if u["events"] else "",
            "finished": any(e["kind"] == "call" and e["name"] == "SubagentHandback" for e in u["events"])
                        or bool(u["spawn_call"] and "result" in u["spawn_call"]),
            "return_first_line": one_line(u["return"]).split(" ⏎ ")[0][:200] if u["return"] else "",
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
        definition = str(Path(root) / "skills" / s["skill"] / "SKILL.md") if root else None
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

    index = {
        "session": session_path.stem, "transcript": str(session_path), "plugin": plugin,
        "plugin_root": root, "plugin_root_exists": bool(root and Path(root).exists()), "version": version,
        "project": main_facts["cwd"], "branch": main_facts["branch"],
        "models": sorted(set(main_facts["models"]) | {m for u in raw_units for m in u["facts"]["models"]}),
        "first_ts": main_events[0]["ts"] if main_events else "", "last_ts": main_events[-1]["ts"] if main_events else "",
        "segments": index_segments, "units": index_units,
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
    (out / "run.md").write_text("\n".join(run), encoding="utf-8")
    print(f"trace: {out}")
    print(f"  plugin root: {root} (version {version}){'' if index['plugin_root_exists'] else ' — MISSING on disk'}")
    print(f"  segments: {len(index_segments)} · units: {len(index_units)} · driver steps: {len(main_events)}")
    for s in index_segments:
        print(f"  seg {s['seg']}: {s['command']} — {len(s['units'])} units spawned directly")


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
    se = sub.add_parser("select")
    se.add_argument("out")
    se.add_argument("--units", default="risk")
    se.add_argument("--cap", type=int, default=12)
    b = sub.add_parser("build")
    b.add_argument("session")
    b.add_argument("--plugin", required=True)
    b.add_argument("--out", required=True)
    b.add_argument("--full", action="store_true")
    a = ap.parse_args()

    if a.cmd == "find":
        import datetime as dt

        hits = sessions_for(a.plugin)[: a.limit]
        if not hits:
            print(f"no session under {PROJECTS} used {a.plugin}")
            return 1
        for s in hits:
            when = dt.datetime.fromtimestamp(s["mtime"]).strftime("%Y-%m-%d %H:%M")
            cmds = ", ".join(dict.fromkeys(c.split(":", 1)[1] for c in s["commands"])) or "—"
            print(f"{s['id']}  {when}  spawns={s['spawns']:<3}  {s['cwd']}  commands: {cmds}")
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

    if a.full:
        for k in LIMITS:
            LIMITS[k] *= 5
    build(resolve(a.session, a.plugin), a.plugin, Path(a.out))
    return 0


if __name__ == "__main__":
    sys.exit(main())
