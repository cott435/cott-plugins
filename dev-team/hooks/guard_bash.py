#!/usr/bin/env python3
"""PreToolUse hook on Bash: a dev-team agent never writes a repo file from the shell.

Input: the hook JSON on stdin (`cwd`, `agent_type`, `tool_input.command`). Exit 0 unless
`<cwd>/docs/architecture.md` exists and `agent_type` starts with `dev-team:`. Refused, exit
2 with the rule on stderr: a redirect (`>`, `>>`, `1>`, `&>`, `>|`) whose target is not
`/dev/null` and not under `.dev-team/tmp/`; `sed -i`; `tee`; `python -c` / `python3 -c`
whose code calls `open(…, "w"|"a"|"x")` or `write_text(`. `2>&1`, `>&2` and `<` are not
writes. Allowed whatever it does: a command whose program is `locked.py`
(`python3 …/locked.py <name> -- <cmd>`), the one way an implementer edits `pyproject.toml`,
`uv.lock` or `.gitignore`. A command the guard cannot parse (`shlex` fails) is let through
with the rule on stderr: a guard fails open, and saying why is the most it can do. Malformed
stdin: exit 0.

The command is split into simple commands on `;`, `&&`, `||`, `|`, `&` and newlines outside
quotes, a here-document's body skipped; each is tokenized with `shlex` (punctuation runs split
into shell operators) and checked on its own, so `pytest -q && echo done > log.txt` is refused
for its second half. Leading `NAME=value` words are not the program; `uv run python` is python.
"""

from __future__ import annotations

import json
import os
import re
import shlex
import sys
from pathlib import Path

RULE = ("Use the Write or Edit tool; a shared edit goes through locked.py; scratch goes under .dev-team/tmp/ "
        "or to /dev/null.")
OPERATORS = re.compile(r"&>>|&>|>>|>\||>&|<<<|<<|<>|<&|&&|\|\||[;&|<>()]")
WRITES = (">", ">>", ">|", "&>", "&>>", "<>")
PYTHON = re.compile(r"python[\d.]*\Z")
PY_WRITE = re.compile(r"open\([^)]*,\s*(?:mode\s*=\s*)?['\"][rwxabt+]*[wax+]"
                      r"|\.open\(\s*(?:mode\s*=\s*)?['\"][rwxabt+]*[wax+]"
                      r"|write_(?:text|bytes)\(")
ASSIGNMENT = re.compile(r"[A-Za-z_]\w*=")


def simple_commands(command: str) -> list[str]:
    """The command's simple commands, split outside quotes; a here-document body is dropped.

    Raises ValueError on an unterminated quote.
    """
    out, cur, i, quote, heredocs = [], "", 0, "", []
    while i < len(command):
        c = command[i]
        if quote:
            cur += c
            if c == "\\" and quote == '"' and i + 1 < len(command):
                cur, i = cur + command[i + 1], i + 1
            elif c == quote:
                quote = ""
        elif c in "'\"":
            quote, cur = c, cur + c
        elif c == "\\" and i + 1 < len(command):
            cur, i = cur + c + command[i + 1], i + 1
        elif c == "<" and command.startswith("<<", i) and not command.startswith("<<<", i):
            m = re.match(r"<<-?\s*(['\"]?)([\w.-]+)\1", command[i:])
            if m:
                heredocs.append(m.group(2))
                cur, i = cur + m.group(0), i + len(m.group(0))
                continue
            cur += c
        elif c == "\n":
            out.append(cur)
            cur = ""
            while heredocs:  # skip each body up to its delimiter line
                end = command.find("\n", i + 1)
                line = command[i + 1:] if end < 0 else command[i + 1:end]
                i = len(command) if end < 0 else end
                if line.strip() == heredocs[0]:
                    heredocs.pop(0)
        elif c in ";|&":
            prev, nxt = command[i - 1] if i else "", command[i + 1] if i + 1 < len(command) else ""
            if c == "&" and (nxt == ">" or prev == ">"):
                cur += c
            elif c == "|" and prev == ">":
                cur += c
            else:
                out.append(cur)
                cur = ""
                if nxt in "&|" and nxt and c != ";":
                    i += 1
        else:
            cur += c
        i += 1
    if quote:
        raise ValueError(f"no closing quotation ({quote})")
    out.append(cur)
    return [c for c in out if c.strip()]


def tokens(simple: str) -> list[str]:
    lex = shlex.shlex(simple, posix=True, punctuation_chars=True)
    lex.whitespace_split = True
    out = []
    for tok in lex:
        out += OPERATORS.findall(tok) if tok and set(tok) <= set("();<>|&") else [tok]
    return out


def _allowed_target(target: str, cwd: Path) -> bool:
    if target == "/dev/null":
        return True
    root = os.path.realpath(cwd)
    path = os.path.realpath(target if os.path.isabs(target) else os.path.join(root, target))
    scratch = os.path.join(root, ".dev-team", "tmp")
    return path == scratch or path.startswith(scratch + os.sep)


def refusal(simple: str, cwd: Path) -> str | None:
    """`<what>: <token>` when this simple command writes a repo file; else None."""
    toks = tokens(simple)
    while toks and ASSIGNMENT.match(toks[0]):
        toks.pop(0)
    if not toks or any(t.endswith("locked.py") for t in toks[:3]):
        return None
    for k, tok in enumerate(toks):
        target = toks[k + 1] if k + 1 < len(toks) else ""
        if tok == ">&" and target and not re.fullmatch(r"\d+|-", target) and not _allowed_target(target, cwd):
            return f"redirect: {target}"
        if tok in WRITES and target and not _allowed_target(target, cwd):
            return f"redirect: {target}"
    program = os.path.basename(toks[0])
    args = [t for t in toks[1:] if t not in WRITES]
    if program == "sed" and any(t.startswith("--in-place") or re.match(r"-[^-]*i", t) for t in args):
        return f"sed -i: {args[-1]}"
    if program == "tee":
        return f"tee: {next((t for t in args if not t.startswith('-')), '(stdout)')}"
    py = 0 if PYTHON.match(program) else next(
        (k for k, t in enumerate(toks[:6]) if PYTHON.match(os.path.basename(t))), None) if program == "uv" else None
    if py is not None and "-c" in toks[py + 1:]:
        k = toks.index("-c", py + 1)
        code = toks[k + 1] if k + 1 < len(toks) else ""
        if m := PY_WRITE.search(code):
            return f"python -c: {m.group(0)}"
    return None


def main() -> int:
    try:
        event = json.loads(sys.stdin.read())
        cwd = Path(event["cwd"])
        agent = event.get("agent_type") or ""
        command = (event.get("tool_input") or {}).get("command") or ""
    except (ValueError, KeyError, TypeError, AttributeError):
        return 0
    if not agent.startswith("dev-team:") or not (cwd / "docs" / "architecture.md").exists():
        return 0
    try:
        if not command.strip():
            raise ValueError("empty command")
        found = next((r for s in simple_commands(command) if (r := refusal(s, cwd))), None)
    except ValueError as e:
        print(f"dev-team bash guard: could not parse the command ({e}); let through. The rule: {agent} never "
              f"writes a repo file from the shell. {RULE}", file=sys.stderr)
        return 0
    if found is None:
        return 0
    print(f"dev-team bash guard: {agent} may not write a repo file from the shell ({found}). {RULE}", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
