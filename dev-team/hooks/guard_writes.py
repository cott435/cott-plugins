#!/usr/bin/env python3
"""PreToolUse hook on Write|Edit: each dev-team role writes only where its job is.

Input: the hook JSON on stdin (`cwd`, `agent_type`, `tool_input.file_path`, and the new text:
`tool_input.content` for Write, `tool_input.old_string` and `new_string` for Edit).

Exit 0 unless `<cwd>/docs/brief.md` or `<cwd>/docs/architecture.md` exists and `agent_type` is
a row of ALLOWED, so `plan-repo`'s agents are guarded before the repo contract is written; the
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
decisions inbox, `docs/packages/<pkg>/decisions/<section>.md`, never `docs/decisions.md`. A
profiler writes the profile under `docs/sources/`, its local folder `.dev-team/data/**`, the
ledgers, the inboxes and `docs/followups.md`.

Suppression comments: a Write or Edit under `**/tests/intent/**` that adds `# noqa`, `# type:
ignore` or `# pragma: no cover` (SUPPRESS, the gate's own patterns) is refused, exit 2. "Adds" is
a count: a Write whose `content` holds more matches than the file on disk (none when it does not
exist), an Edit whose `new_string` holds more than its `old_string`; an edit that keeps an
existing comment in place passes. An event with no `content` or `new_string` skips the check and
the path rule decides alone.

Memory index: a Write of an existing `.claude/agent-memory/<role>/MEMORY.md` whose `content`
lacks a non-blank line the file on disk holds is refused for every guarded role, exit 2. Agents
of one role run in parallel and each adds its line with the Edit tool; a whole-file Write drops
the lines another run just added. A Write that keeps every line passes, and so does any Edit.

Example rows: a Write or Edit that would leave a data profile's `docs/sources/<token>.sample.json`
over 200 KB is refused for every guarded role, exit 2. A profile's file is one the profiler
writes, or one whose sibling `<token>.md` has a `— stage —` title line; a researcher's api sample
is not one. An Edit's size is computed (the file on disk, less `old_string`, plus `new_string`;
`replace_all` is not modelled, and `status.py --run-gate` checks the file on disk). An event with
no text passes this rule, which runs before the path rule.

Section scope: an implementer whose spawn prompt carries `Section: <pkg>/<section>` (read from
its transcript by `status.cached_section`) may write only its section's files, SECTION_SCOPE:
the section's path from the package contract and everything under it, its
`tests/unit/<section>/`, `**/tests/fixtures/**`, its ledger (new and old paths, and
`docs/deviations.md`), its inbox, `.dev-team/tmp/**`, its stop marker
`.dev-team/stop/<pkg>/<section>`, and for `surface` also `docs/packages/<pkg>/interface.md`,
the API page `docs/api/<pkg>/index.md` (and the pre-2.2 `docs/api/<pkg>.md`), the package's own
`<package root>/pyproject.toml` (its `[project.scripts]`), the root `pyproject.toml` and
`mkdocs.yml`. A path under another section's `path` is that section's, whatever the globs say;
for `surface` that is every sibling, and for a parent section its nested ones. It is refused
before the globs are tried. An entry point in the package `pyproject.toml` goes through
`locked.py` and `entry_point.py`, so no section but `surface` has the file in scope. A
`Scaffold:` run, a transcript with no `Section:` line or none readable, or a section the
contract does not list falls back to the role-wide rule.
"""

from __future__ import annotations

import json
import os
import re
import sys
from pathlib import Path

INTENT = "**/tests/intent/**"
MEMORY = ".claude/agent-memory/**"
MEMORY_INDEX = ".claude/agent-memory/*/MEMORY.md"

LEDGERS = ("docs/deviations.md", "docs/deviations/**", "docs/packages/*/deviations/**")
INBOXES = ("docs/packages/*/decisions/**",)
REVIEWS = ("docs/reviews/**", "docs/packages/*/reviews/**")

SAMPLE = "docs/sources/*.sample.json"
SAMPLE_CAP = 200 * 1024
STAGE_TITLE = re.compile(r"# Source probe — .+ — stage — ")

# agent_type → (allowed, excluded, carved back out of the exclusions).
ALLOWED: dict[str, tuple[tuple[str, ...], tuple[str, ...], tuple[str, ...]]] = {
    "dev-team:architect": (("docs/**",), ("docs/packages/*/design/**", *REVIEWS), LEDGERS),
    "dev-team:designer": (("docs/packages/*/design/**", *LEDGERS, *INBOXES), (), ()),
    "dev-team:researcher": (("docs/sources/**", ".claude/skills/*/**"), (), ()),
    "dev-team:profiler": (("docs/sources/**", ".dev-team/data/**", *LEDGERS, *INBOXES, "docs/followups.md"), (), ()),
    "dev-team:tester": ((INTENT, "**/tests/fixtures/**", *LEDGERS), (), ()),
    "dev-team:reviewer": ((*REVIEWS, *LEDGERS, "docs/followups.md"), (), ()),
    "dev-team:documenter": (("README.md", "packages/*/README.md", "docs/index.md", "docs/readme-previous.md",
                             "docs/packages/*/readme-previous.md"), (), ()),
    "dev-team:curator": (("docs/legacy/**", ".claude/skills/*/**"), (), ()),
    "dev-team:implementer": (("**",), ("docs/**",),
                             (*LEDGERS, *INBOXES, "docs/packages/*/interface.md", "docs/api/*.md", "docs/api/*/index.md")),
}
SHARED = "Shared edits — pyproject.toml (dependencies, entry points), uv.lock, .gitignore — go through locked.py."

# The gate's ADDED patterns (gate_on_stop.py): a suppression comment an intent test may not gain.
SUPPRESS = (
    ("# noqa", re.compile(r"#\s*noqa\b", re.I)),
    ("# type: ignore", re.compile(r"#\s*type:\s*ignore\b")),
    ("# pragma: no cover", re.compile(r"#\s*pragma:\s*no\s*cover\b")),
)
SUPPRESS_RULE = ("Write the assertion the design supports; a check that still fires is a `Not written:` line, "
                 "and an Exceptions row is the user's call.")


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
        scope += (f"docs/packages/{pkg}/interface.md", f"docs/api/{pkg}/index.md", f"docs/api/{pkg}.md",
                  f"{package_root}/pyproject.toml", "pyproject.toml", "mkdocs.yml")
    return scope


def added_suppression(event: dict, path: str) -> str | None:
    """The first SUPPRESS item the write adds to an intent test (more matches new than old); else None."""
    ti = event.get("tool_input") or {}
    if isinstance(ti.get("content"), str):
        new = ti["content"]
        try:
            old = Path(path).read_text() if os.path.isfile(path) else ""
        except (OSError, UnicodeDecodeError):
            old = ""
    elif isinstance(ti.get("new_string"), str):
        new, old = ti["new_string"], ti.get("old_string") or ""
    else:
        return None  # no text to judge: fail open, the path rule decides alone
    return next((item for item, rx in SUPPRESS if len(rx.findall(new)) > len(rx.findall(old))), None)


def dropped_index_lines(event: dict, path: str) -> int:
    """How many non-blank lines of the index on disk a Write's `content` lacks; 0 for an Edit."""
    content = (event.get("tool_input") or {}).get("content")
    if not isinstance(content, str) or not os.path.isfile(path):
        return 0
    try:
        old = Path(path).read_text()
    except (OSError, UnicodeDecodeError):
        return 0
    kept = {line.rstrip() for line in content.splitlines()}
    return sum(1 for line in old.splitlines() if line.strip() and line.rstrip() not in kept)


def profile_sample(agent: str, path: str) -> bool:
    """True when path is a data profile's example rows: the profiler writes it, or its sibling
    `<token>.md` exists and its first line is a `— stage —` title."""
    if agent == "dev-team:profiler":
        return True
    doc = Path(path.removesuffix(".sample.json") + ".md")
    try:
        with doc.open(encoding="utf-8") as f:
            return STAGE_TITLE.match(f.readline()) is not None
    except (OSError, UnicodeDecodeError):
        return False


def new_size(event: dict, path: str) -> int:
    """Bytes the file would hold after the write: a Write's content; for an Edit the size on disk
    (0 when absent) less old_string plus new_string; 0 with no text."""
    ti = event.get("tool_input") or {}
    if isinstance(ti.get("content"), str):
        return len(ti["content"].encode())
    if isinstance(ti.get("new_string"), str):
        on_disk = os.path.getsize(path) if os.path.isfile(path) else 0
        return on_disk - len((ti.get("old_string") or "").encode()) + len(ti["new_string"].encode())
    return 0


def section_scope(event: dict, cwd: Path) -> tuple[str, str, tuple[str, ...], list[tuple[str, str]]] | None:
    """(pkg, section, globs, nested) for an implementer spawned on a section the contract lists; else
    None. nested is (section, path) for every other section whose path lies under this one's."""
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
        prefix = row["path"].rstrip("/") + "/"
        nested = [(r["section"], r["path"]) for r in status.sections(pkg)
                  if r["section"] != section and r["path"].startswith(prefix)]
        return pkg, section, SECTION_SCOPE(pkg, section, row, root), nested
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
    if agent not in ALLOWED or not raw or not any((cwd / "docs" / f).exists() for f in ("brief.md", "architecture.md")):
        return 0
    root = os.path.realpath(cwd)
    path = os.path.realpath(raw if os.path.isabs(raw) else os.path.join(cwd, raw))
    rel = os.path.relpath(path, root).replace(os.sep, "/")
    outside = rel == ".." or rel.startswith("../")
    shown = raw if outside else rel
    if not outside and _match(SAMPLE, rel) and profile_sample(agent, path) and (size := new_size(event, path)) > SAMPLE_CAP:
        print(f"dev-team write guard: {shown} would be {size // 1024} KB. A profile's example rows stay under 200 KB: "
              "five rows per kind, and the full failing set under .dev-team/data/.", file=sys.stderr)
        return 2
    if not outside and _match(MEMORY_INDEX, rel) and (dropped := dropped_index_lines(event, path)):
        print(f"dev-team write guard: {agent} may not rewrite {shown}: it would drop {dropped} line(s) another run "
              "may have just added. Add your line with the Edit tool; never rewrite the index.", file=sys.stderr)
        return 2
    scoped = section_scope(event, cwd) if agent == "dev-team:implementer" else None
    if scoped is not None:
        pkg, section, scope, nested = scoped
        other = next((s for s, p in nested if not outside and (rel == p or rel.startswith(p.rstrip("/") + "/"))), None)
        if other is not None:
            print(f"dev-team write guard: {agent} ({pkg}/{section}) may not write {shown}: it is {pkg}/{other}'s. "
                  f"{SHARED}", file=sys.stderr)
            return 2
        if not outside and (_match(MEMORY, rel) or (not _match(INTENT, rel) and any(_match(g, rel) for g in scope))):
            return 0
        files = ", ".join(scope)
        print(f"dev-team write guard: {agent} ({pkg}/{section}) may not write {shown}. Its section's files: {files} "
              f"(and {MEMORY}). {SHARED}", file=sys.stderr)
        return 2
    if not outside and allowed(agent, rel):
        item = added_suppression(event, path) if _match(INTENT, rel) else None
        if item is None:
            return 0
        print(f"dev-team write guard: {agent} may not add `{item}` under tests/intent/ ({shown}). {SUPPRESS_RULE}",
              file=sys.stderr)
        return 2
    allow, exclude, carve = ALLOWED[agent]
    rule = ", ".join(allow) + (f" except {', '.join(exclude)}" if exclude else "")
    rule += f" (but {', '.join(carve)})" if carve else ""
    if agent != "dev-team:tester":
        rule += f"; never {INTENT}"
    print(f"dev-team write guard: {agent} may not write {shown}. Allowed: {rule} (and {MEMORY}).", file=sys.stderr)
    return 2

if __name__ == "__main__":
    sys.exit(main())
