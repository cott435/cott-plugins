#!/usr/bin/env python3
"""Turn a headless driver run's `stream.jsonl` into raw evidence in its `outputs/`.

    python3 collect_stream.py <stream.jsonl> <outputs>

Run by whoever ran the executor (the runner), after its `claude -p --output-format stream-json
--verbose` session has ended — never by the executor, which cannot see its own stream. What it
writes is read from the session's tool calls as they were made, so an expectation that reads
it does not rest on what the executor chose to write down. Only the driver's own calls are
taken (events with no `parent_tool_use_id`); the agents it spawns are not the driver.

- `agent-calls.md` — every Agent call, in order: its batch (the calls of one assistant
  message), `subagent_type`, `run_in_background`, the prompt verbatim in a `~~~~` fence, and
  the first line of what came back.
- `driver-log.txt` — every driver tool call, in order: `Bash` with its command and its output
  (each output cut at 20000 characters, the cut said), `Read`, `Write`, `Edit`, `Glob`,
  `Grep` with their paths, and one `[[collect_stream]] batch <n> sent` line per Agent batch naming each call's
  `subagent_type` and its `Section:`, `Mode:`, `Round:` and `Focus:` lines.
- `reads.txt` — one line per `Read`, `Glob` or `Grep`: the tool, then the path (and pattern).
- `writes.txt` — one line per `Write`, `Edit`, `MultiEdit` or `NotebookEdit`: the tool, then
  the path.
- `bash.txt` — every `Bash` command, whole, one block each, for a read or write made with
  `cat`, `grep`, `sed`, a redirect or a here-document, which `reads.txt` and `writes.txt` do
  not see.
"""
from __future__ import annotations

import json
import re
import sys
from pathlib import Path

CUT = 20000
FIELDS = ("Section", "Mode", "Round", "Focus", "Letter", "Package")


def text_of(content) -> str:
    if isinstance(content, str):
        return content
    if isinstance(content, list):
        return "\n".join(b.get("text", "") for b in content if isinstance(b, dict))
    return ""


def main(stream: Path, outputs: Path) -> None:
    calls: list[dict] = []  # in order: {id, msg, name, input}
    results: dict[str, str] = {}
    for line in stream.read_text().splitlines():
        try:
            event = json.loads(line)
        except ValueError:
            continue
        if event.get("parent_tool_use_id") is not None:
            continue
        message = event.get("message") if isinstance(event.get("message"), dict) else {}
        content = message.get("content")
        if event.get("type") == "assistant" and isinstance(content, list):
            for block in content:
                if block.get("type") == "tool_use":
                    calls.append({"id": block["id"], "msg": message.get("id"), "name": block["name"],
                                  "input": block.get("input") or {}})
        elif event.get("type") == "user" and isinstance(content, list):
            for block in content:
                if block.get("type") == "tool_result":
                    results[block.get("tool_use_id")] = text_of(block.get("content"))

    outputs.mkdir(parents=True, exist_ok=True)
    batches: dict[str, int] = {}
    agent_md = ["# Agent calls — from the session's stream (collect_stream.py)", ""]
    log, reads, writes, bash = [], [], [], []
    n_agent = 0
    for call in calls:
        name, inp, back = call["name"], call["input"], results.get(call["id"], "")
        if name in ("Agent", "Task"):
            new = call["msg"] not in batches
            batch = batches.setdefault(call["msg"], len(batches) + 1)
            n_agent += 1
            prompt = inp.get("prompt", "")
            first = next((l for l in back.splitlines() if l.strip() and not l.startswith("[Subagent")), "")
            agent_md += [f"## {n_agent} · batch {batch} · {inp.get('subagent_type')} · "
                         f"run_in_background={str(inp.get('run_in_background', False)).lower()}", "",
                         "~~~~", prompt, "~~~~", "", f"Returned, first line: {first.strip()}", ""]
            fields = " · ".join(f"{m.group(1)}: {m.group(2).strip()}" for m in
                                re.finditer(rf"^({'|'.join(FIELDS)}): (.*)$", prompt, re.M))
            if new:
                log.append(f"[[collect_stream]] batch {batch} sent")
            log.append(f"[[collect_stream]] batch {batch} call {n_agent}: {inp.get('subagent_type')} · {fields}")
        elif name == "Bash":
            command = inp.get("command", "")
            bash += [f"## {len(bash) + 1}", command, ""]
            out = back if len(back) <= CUT else back[:CUT] + f"\n[… cut by collect_stream.py: {len(back)} characters in all]"
            log += [f"--- Bash", "$ " + command.replace("\n", "\n  "), out, ""]
        else:
            path = inp.get("file_path") or inp.get("notebook_path") or inp.get("path") or ""
            extra = f"\t{inp['pattern']}" if "pattern" in inp else ""
            log.append(f"--- {name} {path}{extra}")
            if name in ("Read", "Glob", "Grep"):
                reads.append(f"{name}\t{path}{extra}")
            elif name in ("Write", "Edit", "MultiEdit", "NotebookEdit"):
                writes.append(f"{name}\t{path}")
    head = "# from the session's stream (collect_stream.py): the driver's own tool calls only\n"
    (outputs / "agent-calls.md").write_text("\n".join(agent_md) + ("" if n_agent else "(no Agent call)\n"))
    (outputs / "driver-log.txt").write_text(head + "\n".join(log) + "\n")
    (outputs / "reads.txt").write_text(head + ("\n".join(reads) or "(none)") + "\n")
    (outputs / "writes.txt").write_text(head + ("\n".join(writes) or "(none)") + "\n")
    (outputs / "bash.txt").write_text(head + ("\n".join(bash) or "(none)") + "\n")
    print(f"collect_stream: {len(calls)} driver tool calls, {n_agent} Agent calls in {len(batches)} batches, "
          f"{len(reads)} reads, {len(writes)} writes → {outputs}")


if __name__ == "__main__":
    if len(sys.argv) != 3:
        sys.exit(__doc__)
    main(Path(sys.argv[1]), Path(sys.argv[2]))
