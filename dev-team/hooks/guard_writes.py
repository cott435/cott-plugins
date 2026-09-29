#!/usr/bin/env python3
"""PreToolUse hook on Write|Edit: each dev-team role writes only where its job is.

Input: the hook JSON on stdin (`cwd`, `agent_type`, `tool_input.file_path`).

Exit 0 unless `<cwd>/docs/architecture.md` exists and `agent_type` is a row of ALLOWED; the
main thread, `Explore`, `general-purpose` and any other agent are never guarded. The path is
made relative to `cwd`; a path outside `cwd` is refused for every guarded role. A path is
allowed when it matches one of the role's globs and none of its exclusions, or one of its
carve-outs from those exclusions (`**` any depth, `*` one segment). `**/tests/intent/**` is the tester's alone, whatever a row says. Every role's
own memory, `.claude/agent-memory/**`, is allowed to all (the agents run with `memory:
project`). A refusal exits 2 with the rule on stderr. Malformed stdin: exit 0.

`<pkg>` in the design's paths is `*` here: the guard knows the role, not the section. The
ledger is `docs/deviations/<pkg>/<section>.md`; the pre-split `docs/deviations.md` stays
writable wherever the ledger is, so an entry is edited in the file that holds it.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

INTENT = "**/tests/intent/**"
MEMORY = ".claude/agent-memory/**"

# agent_type → (allowed, excluded, carved back out of the exclusions).
ALLOWED: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
    "dev-team:architect": (("docs/**",), ("docs/packages/*/design/**", "docs/reviews/**"), ("docs/deviations.md", "docs/deviations/**")),
    "dev-team:designer": (("docs/packages/*/design/**", "docs/deviations.md", "docs/deviations/**", "docs/decisions.md"), (), ()),
    "dev-team:researcher": (("docs/sources/**", ".claude/skills/*/**"), (), ()),
    "dev-team:tester": ((INTENT, "**/tests/fixtures/**", "docs/deviations.md", "docs/deviations/**"), (), ()),
    "dev-team:reviewer": (("docs/reviews/**", "docs/deviations.md", "docs/deviations/**", "docs/followups.md"), (), ()),
    "dev-team:documenter": (("README.md", "packages/*/README.md", "docs/index.md", "docs/readme-previous.md",
                             "docs/packages/*/readme-previous.md"), (), ()),
    "dev-team:curator": (("docs/legacy/**", ".claude/skills/*/**"), (), ()),
    "dev-team:implementer": (("**",), ("docs/**",),
                             ("docs/deviations.md", "docs/deviations/**", "docs/decisions.md", "docs/packages/*/interface.md", "docs/api/*.md")),
}


def _regex(glob: str) -> re.Pattern[str]:
    """`**/` any leading directories (or none), `**` anything, `*` one path segment."""
    out, i = "", 0
    while i < len(glob):
        if glob.startswith("**/", i):
            out, i = out + "(?:.*/)?", i + 3
        elif glob.startswith("**", i):
            out, i = out + ".*", i + 2
        elif glob[i] == "*":
            out, i = out + "[^/]*", i + 1
        elif glob[i] == "?":
            out, i = out + "[^/]", i + 1
        else:
            out, i = out + re.escape(glob[i]), i + 1
    return re.compile(out + r"\Z")


def _match(glob: str, rel: str) -> bool:
    return _regex(glob).match(rel) is not None


def allowed(agent: str, rel: str) -> bool:
    if _match(MEMORY, rel):
        return True
    if _match(INTENT, rel):
        return agent == "dev-team:tester"
    allow, exclude, carve = ALLOWED[agent]
    if any(_match(g, rel) for g in carve):
        return True
    return any(_match(g, rel) for g in allow) and not any(_match(g, rel) for g in exclude)


def main() -> int:
    try:
        event = json.loads(sys.stdin.read())
        cwd = Path(event["cwd"])
        agent = event.get("agent_type") or ""
        raw = (event.get("tool_input") or {}).get("file_path") or ""
    except (ValueError, KeyError, TypeError, AttributeError):
        return 0
    if agent not in ALLOWED or not (cwd / "docs" / "architecture.md").exists() or not raw:
        return 0
    root = os.path.realpath(cwd)
    path = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(cwd, raw))
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    outside = rel == ".." or rel.startswith("../")
    if not outside and allowed(agent, rel):
        return 0
    shown = raw if outside else rel
    allow, exclude, carve = ALLOWED[agent]
    rule = ", ".join(allow) + (f" except {', '.join(exclude)}" if exclude else "")
    rule += f" (but {', '.join(carve)})" if carve else ""
    if agent != "dev-team:tester":
        rule += f"; never {INTENT}"
    print(f"dev-team write guard: {agent} may not write {shown}. Allowed: {rule} (and {MEMORY}).", file=sys.stderr)
    return 2


if __name__ == "__main__":
    sys.exit(main())
