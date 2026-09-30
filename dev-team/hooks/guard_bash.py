#!/usr/bin/env python3
"""PreToolUse hook on Bash: a dev-team agent never writes a repo file from the shell.

Input: the hook JSON on stdin (`cwd`, `agent_type`, `tool_input.command`). Exit 0 unless
`<cwd>/docs/architecture.md` exists and `agent_type` starts with `dev-team:`. Refused, exit
2 with the rule on stderr: a redirect (`>`, `>>`, `1>`, `&>`, `>|`) whose target is not
`/dev/null` and not under `.dev-team/tmp/`; `sed -i`; `tee`; `python -c` / `python3 -c`
whose code calls `open(…, "w"|"a"|"x")` or `write_text(`, and the same check on the
here-document body of a python whose script is `-`, or that has no script and a
here-document (`python3 - <<'EOF'`); `sh -c`, `bash -c` and `zsh -c` scripts are checked as
commands of their own. `2>&1`, `>&2` and `<` are not writes. `locked.py`
(`python3 …/locked.py <name> -- <cmd>`) is the one way an implementer edits `pyproject.toml`,
`uv.lock` or `.gitignore`, and it exempts only those edits: the command after `--` is `uv add`,
`uv remove`, `uv lock` or `uv sync`, or `sh -c` whose script is one `printf … >> .gitignore`;
any other wrapped command is checked as if it were not wrapped. A command the guard cannot
parse (`shlex` fails) is let through with the rule on stderr: a guard fails open, and saying
why is the most it can do. Malformed stdin: exit 0.

The command is split into simple commands on `;`, `&&`, `||`, `|`, `&` and newlines outside
quotes, a here-document's body kept aside for the command that opened it; each is tokenized with `shlex` (punctuation runs split
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
SHELLS = ("sh", "bash", "zsh")
LOCKED_UV = ("add", "remove", "lock", "sync")


def simple_commands(command: str) -> list[str]:
    """The command's simple commands, split outside quotes; a here-document body is dropped."""
    return [c for c, _ in split_commands(command)]


def split_commands(command: str) -> list[tuple[str, list[str]]]:
    """(simple command, the bodies of the here-documents it opened), split outside quotes.

    Raises ValueError on an unterminated quote.
    """
    out: list[str] = []
    bodies: dict[int, list[str]] = {}
    cur, i, quote, heredocs = "", 0, "", []
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
                heredocs.append((m.group(2), len(out), []))
                cur, i = cur + m.group(0), i + len(m.group(0))
                continue
            cur += c
        elif c == "\n":
            out.append(cur)
            cur = ""
            while heredocs:  # set each body aside, up to its delimiter line
                end = command.find("\n", i + 1)
                line = command[i + 1:] if end < 0 else command[i + 1:end]
                i = len(command) if end < 0 else end
                delim, owner, body = heredocs[0]
                if line.strip() == delim:
                    bodies.setdefault(owner, []).append("\n".join(body))
                    heredocs.pop(0)
                else:
                    body.append(line)
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
    for _, owner, body in heredocs:  # a body the command ended inside
        bodies.setdefault(owner, []).append("\n".join(body))
    return [(c, bodies.get(k, [])) for k, c in enumerate(out) if c.strip()]


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


def _script_refusal(script: str, cwd: Path) -> str | None:
    """The first refusal among a shell script's simple commands."""
    return next((r for c, b in split_commands(script) if (r := refusal(c, cwd, b))), None)


def _gitignore_printf(script: str) -> bool:
    """True for a script that is one `printf … >> .gitignore` and nothing else."""
    cmds = split_commands(script)
    if len(cmds) != 1 or cmds[0][1]:
        return False
    toks = tokens(cmds[0][0])
    writes = [(t, toks[k + 1] if k + 1 < len(toks) else "") for k, t in enumerate(toks) if t in WRITES or t == ">&"]
    return bool(toks) and toks[0] == "printf" and writes == [(">>", ".gitignore")]


def _locked(toks: list[str], cwd: Path) -> str | None:
    """A `locked.py <name> -- <cmd>` command: None when <cmd> is one of the shared edits locked.py
    exists for, else <cmd>'s own refusal."""
    inner = toks[toks.index("--") + 1:] if "--" in toks else []
    if len(inner) >= 2 and inner[0] == "uv" and inner[1] in LOCKED_UV:
        return None
    if len(inner) == 3 and inner[0] in SHELLS and inner[1] == "-c" and _gitignore_printf(inner[2]):
        return None
    return _refusal(inner, cwd, []) if inner else None


def refusal(simple: str, cwd: Path, bodies: list[str] | None = None) -> str | None:
    """`<what>: <token>` when this simple command writes a repo file; else None."""
    return _refusal(tokens(simple), cwd, bodies or [])


def _refusal(toks: list[str], cwd: Path, bodies: list[str]) -> str | None:
    toks = list(toks)
    while toks and ASSIGNMENT.match(toks[0]):
        toks.pop(0)
    if not toks:
        return None
    if any(t.endswith("locked.py") for t in toks[:3]):
        return _locked(toks, cwd)
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
    elif py is not None and bodies:
        script = next((t for t in toks[py + 1:] if not t.startswith("-") or t == "-" or set(t) <= set("<>&|")), None)
        if script is None or script == "-" or set(script) <= set("<>&|"):
            for body in bodies:
                if m := PY_WRITE.search(body):
                    return f"python stdin script: {m.group(0)}"
    if program in SHELLS and "-c" in toks[1:]:
        k = toks.index("-c", 1)
        if k + 1 < len(toks):
            return _script_refusal(toks[k + 1], cwd)
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
        found = _script_refusal(command, cwd)
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
