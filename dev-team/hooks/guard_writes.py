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

`<pkg>` in the design's paths is `*` here: the role-wide rule knows the role, not the section.
New entries go to `docs/packages/<pkg>/deviations/<section>.md`, reports to
`docs/packages/<pkg>/reviews/<section>/`; the old ledgers (`docs/deviations/<pkg>/<section>.md`,
the pre-split `docs/deviations.md`) and `docs/reviews/` stay writable wherever the new ones are,
so an entry is edited in the file that holds it. A designer or implementer writes its section's
decisions inbox, `docs/packages/<pkg>/decisions/<section>.md`, never `docs/decisions.md`.

Section scope: an implementer whose spawn prompt carries `Section: <pkg>/<section>` (read from
its transcript by `status.cached_section`) may write only its section's files, SECTION_SCOPE:
the section's path from the package contract and everything under it, its
`tests/unit/<section>/`, `**/tests/fixtures/**`, its ledger (new and old paths, and
`docs/deviations.md`), its inbox, `.dev-team/tmp/**`, its stop marker
`.dev-team/stop/<pkg>/<section>`, and for `surface` also `docs/packages/<pkg>/interface.md`,
`docs/api/<pkg>.md`, the root `pyproject.toml` and `mkdocs.yml`. A `Scaffold:` run, a
transcript with no `Section:` line or none readable, or a section the contract does not list
falls back to the role-wide rule.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

INTENT = "**/tests/intent/**"
MEMORY = ".claude/agent-memory/**"

LEDGERS = ("docs/deviations.md", "docs/deviations/**", "docs/packages/*/deviations/**")
INBOXES = ("docs/packages/*/decisions/**",)
REVIEWS = ("docs/reviews/**", "docs/packages/*/reviews/**")

# agent_type → (allowed, excluded, carved back out of the exclusions).
ALLOWED: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
    "dev-team:architect": (("docs/**",), ("docs/packages/*/design/**", *REVIEWS), LEDGERS),
    "dev-team:designer": (("docs/packages/*/design/**", *LEDGERS, *INBOXES), (), ()),
    "dev-team:researcher": (("docs/sources/**", ".claude/skills/*/**"), (), ()),
    "dev-team:tester": ((INTENT, "**/tests/fixtures/**", *LEDGERS), (), ()),
    "dev-team:reviewer": ((*REVIEWS, *LEDGERS, "docs/followups.md"), (), ()),
    "dev-team:documenter": (("README.md", "packages/*/README.md", "docs/index.md", "docs/readme-previous.md",
                             "docs/packages/*/readme-previous.md"), (), ()),
    "dev-team:curator": (("docs/legacy/**", ".claude/skills/*/**"), (), ()),
    "dev-team:implementer": (("**",), ("docs/**",),
                             (*LEDGERS, *INBOXES, "docs/packages/*/interface.md", "docs/api/*.md")),
}
SHARED = "Shared edits — pyproject.toml, uv.lock, .gitignore — go through locked.py."


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


def SECTION_SCOPE(pkg: str, section: str, row: dict[str, str], package_root: str) -> tuple[str, ...]:
    """The globs an implementer building <pkg>/<section> may write (memory aside)."""
    unit = f"{package_root}/tests/unit/{section}/**" if package_root != "." else f"tests/unit/{section}/**"
    scope = (row["path"], f"{row['path']}/**", unit, "**/tests/fixtures/**",
             f"docs/packages/{pkg}/deviations/{section}.md", f"docs/deviations/{pkg}/{section}.md", "docs/deviations.md",
             f"docs/packages/{pkg}/decisions/{section}.md", ".dev-team/tmp/**", f".dev-team/stop/{pkg}/{section}")
    if section == "surface":
        scope += (f"docs/packages/{pkg}/interface.md", f"docs/api/{pkg}.md", "pyproject.toml", "mkdocs.yml")
    return scope


def section_scope(event: dict, cwd: Path) -> tuple[str, str, tuple[str, ...]] | None:
    """(pkg, section, globs) for an implementer spawned on a section the contract lists; else None."""
    try:
        plugin = Path(os.environ.get("CLAUDE_PLUGIN_ROOT") or Path(__file__).resolve().parents[1])
        sys.path.insert(0, str(plugin / "skills" / "status" / "scripts"))
        sys.dont_write_bytecode = True  # no __pycache__ inside the installed plugin
        import status

        status.set_root(cwd)
        target = status.cached_section(event)
        if target is None:
            return None
        pkg, section = target
        row = status._row(pkg, section)
        if row is None:
            return None
        root = os.path.relpath(os.path.realpath(status.package_root(pkg)), os.path.realpath(cwd)).replace(os.sep, "/")
        return pkg, section, SECTION_SCOPE(pkg, section, row, root)
    except Exception:  # a guard that cannot read the section keeps the role-wide rule
        return None


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
    shown = raw if outside else rel
    scoped = section_scope(event, cwd) if agent == "dev-team:implementer" else None
    if scoped is not None:
        pkg, section, scope = scoped
        if not outside and (_match(MEMORY, rel) or (not _match(INTENT, rel) and any(_match(g, rel) for g in scope))):
            return 0
        files = ", ".join(scope)
        print(f"dev-team write guard: {agent} ({pkg}/{section}) may not write {shown}. Its section's files: {files} "
              f"(and {MEMORY}). {SHARED}", file=sys.stderr)
        return 2
    if not outside and allowed(agent, rel):
        return 0
    allow, exclude, carve = ALLOWED[agent]
    rule = ", ".join(allow) + (f" except {', '.join(exclude)}" if exclude else "")
    rule += f" (but {', '.join(carve)})" if carve else ""
    if agent != "dev-team:tester":
        rule += f"; never {INTENT}"
    print(f"dev-team write guard: {agent} may not write {shown}. Allowed: {rule} (and {MEMORY}).", file=sys.stderr)
    return 2

if __name__ == "__main__":
    sys.exit(main())
