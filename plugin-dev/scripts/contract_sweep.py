#!/usr/bin/env python3
"""Check the cross-file claims a plugin's agents act on and nothing else verifies.

A plugin is a set of prompts that reference each other by name: one agent owns a document
template, others parse it by heading; one skill forbids something another still describes.
Nothing fails when those drift — the agent just reads for a heading that is never written.
This runner checks the claims a bundle declares in its own `contracts.yml`.

Five kinds of claim, all of them about file contents, so all of them decidable without
running a model:

  forbid        a pattern that must not appear (a rule one file states and another breaks),
                its exemptions scoped to the whole line or, with <near>, to each match
  headings      every heading a reader parses is one the owner's template defines, read from
                its numbered **bold** items or, with <owner_form: markdown>, its `##` headings
  names_listed  every directory under <dirs> has its name in <file> (a list that goes stale),
                narrowed by <where> on frontmatter and read in one of three <form>s
  frontmatter   every frontmatter key in <files> is one plugin-anatomy documents for <kind>
                (skill or agent), and none is a key plugins ignore
  flow          the `flow:` block of <file> (site/site.yml), which the site's flow page is
                drawn from, agrees with the files: every skill a role's file names is
                declared for it and every declared one is named; every role a document
                lists names that document and every role that names it is listed; every
                script and hook a driver names exists and every wired hook is named

Usage:  python3 contract_sweep.py [bundle] [--quiet]
Exits 1 if any case fails, 0 if all pass, 2 if the bundle has no contracts.yml.

`contracts.yml` lives at the bundle root. See the check-contracts skill for the schema and a
worked example; `--help` prints it too.
"""

from __future__ import annotations

import fnmatch
import re
import sys
from pathlib import Path

# Authored files only. Generated mirrors (site/docs/) would double every finding, and a
# finding there is fixed in the source anyway.
DEFAULT_FILES = ["agents/*.md", "skills/**/*.md", "rules/*.md", "README.md", "CLAUDE.md",
                 "site/*.md", "site/workflows/*.md", "site/notes/*.md", "skills/**/*.py"]


def authored(bundle: Path, globs: list[str]) -> list[Path]:
    """Every existing file matching any glob, once, in a stable order."""
    out: dict[Path, None] = {}
    for g in globs:
        for p in sorted(bundle.glob(g)):
            if p.is_file() and "/site/docs/" not in p.as_posix():
                out[p] = None
    return list(out)


def span(text: str, bounds: list | None, where: str) -> str:
    """The slice of text between two literal markers. bounds is [start, end]; end may be null."""
    if not bounds:
        return text
    start, end = (bounds + [None])[:2]
    if start not in text:
        raise LookupError(f"{where}: marker not found: {start!r}")
    i = text.index(start)
    if not end:
        return text[i:]
    if end not in text[i:]:
        raise LookupError(f"{where}: end marker not found after start: {end!r}")
    return text[i:text.index(end, i)]


def template_items(block: str) -> set[str]:
    """Names of a numbered, bolded template: `3. **CLI commands** — table: …` -> {CLI commands}."""
    return {" ".join(m.group(1).split()) for m in re.finditer(r"^\d+\. \*\*(.+?)\*\*", block, re.M)}


def bolded(block: str) -> set[str]:
    """Every **Bolded Name** in a block, whitespace collapsed so a line break does not hide one."""
    return {" ".join(m.group(1).split()) for m in re.finditer(r"\*\*([A-Z][^*]{2,40})\*\*", block)}


def check_forbid(bundle: Path, spec: dict) -> tuple[bool, str]:
    """A match of `pattern` (with every `all_of` in scope) is a failure unless `unless` is too.

    Scope is the whole line by default. `near: <n>` narrows it to the matched text plus n
    characters either side, which is what an exemption almost always means: a pardon for the
    occurrence it describes, not for every other occurrence that shares its line. Without it,
    one exempt phrase pardons anything written beside it — and an exemption tends to live
    exactly where the thing it pardons is discussed, so that is where a violation would land.
    """
    pattern = re.compile(spec["pattern"])
    unless = [re.compile(u) for u in spec.get("unless", [])]
    all_of = spec.get("all_of", [])
    near = spec.get("near")
    hits = []
    for p in authored(bundle, spec.get("files", DEFAULT_FILES)):
        for n, line in enumerate(p.read_text(errors="ignore").splitlines(), 1):
            for m in pattern.finditer(line):
                scope = line if not near else line[max(0, m.start() - near):m.end() + near]
                if any(a not in scope for a in all_of) or any(u.search(scope) for u in unless):
                    continue
                hits.append(f"{p.relative_to(bundle)}:{n}")
                break
    return not hits, ", ".join(hits) or "0 matches"


def markdown_headings(block: str) -> set[str]:
    """Level-2 Markdown headings: `## Build order` -> {Build order}. Fenced code is skipped."""
    block = re.sub(r"(?ms)^```.*?^```", "", block)
    return {" ".join(m.group(1).split()) for m in re.finditer(r"^## (.+?)\s*$", block, re.M)}


def check_headings(bundle: Path, spec: dict) -> tuple[bool, str]:
    """Every heading a reader names is one the owner's template defines.

    The owner is a numbered **bold** list by default, or with `owner_form: markdown` a file
    whose own `##` headings are the template, such as a document template.
    """
    owner = bundle / spec["owner"]
    block = span(owner.read_text(), spec.get("owner_span"), spec["owner"])
    markdown = spec.get("owner_form") == "markdown"
    owned = markdown_headings(block) if markdown else template_items(block)
    if not owned:
        kind = "`##` headings" if markdown else "numbered template items"
        return False, f"{spec['owner']}: no {kind} found in the owner span"
    bad, counted = [], 0
    for reader in spec["readers"]:
        path = bundle / reader["file"]
        text = path.read_text()
        named = bolded(span(text, reader.get("span"), reader["file"])) if reader.get("span") else set()
        named |= {" ".join(c.split()) for c in reader.get("cites", [])}
        counted += len(named)
        for h in sorted(named):
            if not any(h.lower() == o.lower() for o in owned):
                bad.append(f"{reader['file']} names '{h}'")
    return not bad, "; ".join(bad) or f"{counted} names across {len(spec['readers'])} readers, all owned"


# How a list cites a name, and how to read the names already in it. `code` is the default:
# a name in backticks, anywhere in the span. `tree` is an indented branch of a directory tree,
# `list` a YAML or Markdown bullet on its own line.
FORMS = {
    "code": (r"`{n}`", r"`([a-z][a-z0-9-]{2,})`"),
    "tree": (r"── {n}/", r"(?m)^ +[├└]── ([a-z][a-z0-9-]+)/"),
    "list": (r"(?m)^ *- +{n} *(?:#.*)?$", r"(?m)^ *- +([a-z][a-z0-9-]+) *(?:#.*)?$"),
}


def frontmatter(path: Path) -> dict:
    """The YAML frontmatter of a Markdown file, or {} when it has none."""
    import yaml
    text = path.read_text(errors="ignore")
    if not text.startswith("---\n"):
        return {}
    end = text.find("\n---", 3)
    return yaml.safe_load(text[4:end]) or {} if end > 0 else {}


def qualifies(d: Path, where: dict) -> bool:
    """A directory counts when its SKILL.md frontmatter matches every key in `where`."""
    fm = frontmatter(d / "SKILL.md")
    return all(fm.get(k) == v for k, v in where.items())


def check_names_listed(bundle: Path, spec: dict) -> tuple[bool, str]:
    """Every directory matching `dirs` has its name inside `file` (optionally within a span).

    `where` narrows the directories to those whose SKILL.md frontmatter matches, so a list
    that covers one class of skill is checked against that class and not all of them.
    """
    listing = bundle / spec["file"]
    block = span(listing.read_text(), spec.get("span"), spec["file"])
    form = spec.get("form", "code")
    if form not in FORMS:
        return False, f"unknown form {form!r}; known: {', '.join(FORMS)}"
    cite, existing = FORMS[form]
    where = spec.get("where") or {}
    names = sorted({p.name for g in [spec["dirs"]] for p in bundle.glob(g.rstrip("/"))
                    if p.is_dir() and qualifies(p, where)})
    if not names:
        return False, f"`dirs: {spec['dirs']}`" + (f" + `where`" if where else "") + " matched no directory"
    missing = [n for n in names if not re.search(cite.format(n=re.escape(n)), block)]
    extra = [w for w in re.findall(existing, block) if w not in names]
    detail = []
    if missing:
        detail.append(f"not listed in {spec['file']}: {', '.join(missing)}")
    if extra:
        detail.append(f"listed but no such directory: {', '.join(sorted(set(extra)))}")
    scope = f"{len(names)} names" + (" matching `where`" if where else "")
    return not detail, "; ".join(detail) or f"{scope}, all listed"


# The allowed frontmatter keys are read from plugin-dev's own plugin-anatomy references, not
# restated here: the reference is the source of truth, and this checker enforces it. The path
# is relative to this script, so a bundle checked with an installed plugin-dev reads the
# installed references.
ANATOMY = Path(__file__).resolve().parent.parent / "skills" / "plugin-anatomy" / "references"
KEY_SOURCES = {"skill": "skills.md", "agent": "agents.md"}


def documented_keys(kind: str) -> tuple[set[str], set[str]]:
    """(allowed, ignored_in_plugins) from the `frontmatter-keys: <kind>` block in plugin-anatomy."""
    import yaml
    if kind not in KEY_SOURCES:
        raise LookupError(f"unknown frontmatter kind {kind!r}; known: {', '.join(KEY_SOURCES)}")
    source = ANATOMY / KEY_SOURCES[kind]
    m = re.search(rf"<!-- frontmatter-keys: {kind} -->\s*```yaml\n(.*?)```", source.read_text(), re.S)
    if not m:
        raise LookupError(f"{source}: no `frontmatter-keys: {kind}` block")
    block = yaml.safe_load(m.group(1)) or {}
    return set(block.get("allowed") or []), set(block.get("ignored_in_plugins") or [])


def check_frontmatter(bundle: Path, spec: dict) -> tuple[bool, str]:
    """Every top-level frontmatter key in `files` is documented for `kind` and honored in plugins.

    A misspelled key (`allowed_tools`) and a key plugins ignore (`hooks` on a plugin agent) fail
    the same way at run time: silently. Both are caught here, at the key's file:line.
    """
    allowed, ignored = documented_keys(spec["kind"])
    files = spec["files"] if isinstance(spec["files"], list) else [spec["files"]]
    bad, checked = [], 0
    for p in authored(bundle, files):
        rel = p.relative_to(bundle)
        text = p.read_text(errors="ignore")
        end = text.find("\n---", 3)
        if not text.startswith("---\n") or end < 0:
            bad.append(f"{rel}: no frontmatter")
            continue
        checked += 1
        for n, line in enumerate(text[4:end].splitlines(), 2):
            m = re.match(r"([A-Za-z_][\w-]*)\s*:", line)
            if not m:
                continue
            key = m.group(1)
            if key in ignored:
                bad.append(f"{rel}:{n} `{key}` is ignored for plugin {spec['kind']}s")
            elif key not in allowed:
                bad.append(f"{rel}:{n} `{key}` is not a documented {spec['kind']} field")
    if not checked and not bad:
        return False, f"`files: {spec['files']}` matched no file"
    return not bad, "; ".join(bad) or f"{checked} files, every key documented"


def _actors(value) -> list[str]:
    """The names in a `flow:` list: plain names, or the keys of `{name: note}` mappings."""
    out: list[str] = []
    for v in value if isinstance(value, list) else [value] if value else []:
        out += [str(k) for k in v] if isinstance(v, dict) else [str(v)]
    return out


def _mention(token: str, literal: bool = False) -> re.Pattern:
    """A path or name as a pattern. In a path, `<x>`, `{x}`, `*` and `…` stand for anything
    without a space, so `docs/<pkg>/x.md` finds `docs/{pkg}/x.md` and `docs/data/x.md`; a
    `match` string is looked for as written."""
    token = token.strip("`")
    pieces = [token] if literal else re.split(r"<[^>]*>|\{[^}]*\}|…|\*", token)
    start = r"(?<![\w-])" if token[:1].isalnum() else ""       # `evals/x` is not inside `run-evals/x`
    return re.compile(start + r"[^\s`'\"]*?".join(re.escape(x) for x in pieces))


def _head(path: Path) -> str:
    """A file's frontmatter as text. Read by line, not as YAML: a description with a colon
    in it is common in agent files and is not valid YAML."""
    m = re.match(r"---\n(.*?)\n---\n", path.read_text(errors="ignore"), re.S)
    return m.group(1) if m else ""


def _preloaded(path: Path) -> set[str]:
    """The skills an agent's `skills:` frontmatter names, inline or as a list."""
    m = re.search(r"^skills:[ \t]*(.*(?:\n[ \t]+-.*)*)", _head(path), re.M)
    return set(re.findall(r"[\w:-]+", m.group(1))) if m else set()


def _first_line(text: str, pattern: re.Pattern) -> int:
    m = pattern.search(text)
    return text.count("\n", 0, m.start()) + 1 if m else 0


def check_flow(bundle: Path, spec: dict) -> tuple[bool, str]:
    """The `flow:` block the flow page is drawn from agrees with the bundle's own files.

    A role's file is `agents/<id>.md`, `skills/<id>/SKILL.md`, or the `file:` its entry
    gives. Every claim is about what that file names, so a role that starts using a skill
    or touching a document fails here until the block places it:

      skills     a model-invocable skill the file names is in the role's `always`,
                 `sometimes` or `names` (it is named, not run), or its agent's `skills:`
                 frontmatter; and each of those three lists names only skills the file names
      documents  a role in a document's `writes` or `reads` names the document (its `path`,
                 or any of its `match` strings, taken as written); a role that names it is in `writes`,
                 `reads` or `names`. `match: false` leaves a document unchecked. A role
                 with `relays: true` hands paths to agents: what it names beyond its own
                 lists is not held against it
      drivers    `skill` is a skill; every `x.py` a driver names is a script in the bundle,
                 and one named in `next` or `writer` is named in the driver's file; every
                 hook script wired in hooks/hooks.json is named in some driver's `held`,
                 and a hook named there is wired
      roles      every agent is a role
    """
    import json
    import yaml
    rel = spec.get("file", "site/site.yml")
    flow = (yaml.safe_load((bundle / rel).read_text()) or {}).get("flow") or {}
    if not flow:
        return False, f"{rel} has no `flow:` block"
    problems: list[str] = []
    agents = {x.stem: x for x in sorted((bundle / "agents").glob("*.md"))}
    skills = {x.parent.name: x for x in sorted((bundle / "skills").glob("*/SKILL.md"))}
    loadable = {n for n, x in skills.items()
                if not re.search(r"^disable-model-invocation:\s*true\s*$", _head(x), re.M)}

    roles: dict[str, tuple[str, str] | None] = {}       # id -> (its file, the file's body)
    relays: set[str] = set()
    for entry in flow.get("roles") or list(agents):
        e = entry if isinstance(entry, dict) else {"id": entry}
        rid = str(e["id"])
        path = bundle / e["file"] if e.get("file") else agents.get(rid) or skills.get(rid)
        if path is not None and not path.is_file():
            problems.append(f"role {rid}: `file: {e['file']}` does not exist")
            path = None
        # The frontmatter is blanked, not cut, so a line number is the file's own.
        body = re.sub(r"\A---\n.*?\n---\n", lambda m: "\n" * m.group(0).count("\n"), path.read_text(),
                      flags=re.S) if path else ""
        roles[rid] = (path.relative_to(bundle).as_posix(), body) if path else None
        if e.get("relays"):
            relays.add(rid)
    for a in agents:
        if a not in roles:
            problems.append(f"agents/{a}.md is not in flow.roles")

    # Skills.
    uses = flow.get("uses") or {}
    for rid in uses:
        if rid not in roles:
            problems.append(f"flow.uses.{rid}: no such role")
    for rid, src in roles.items():
        use = uses.get(rid) or {}
        ran = set(_actors(use.get("always"))) | set(_actors(use.get("sometimes")))
        named = set(_actors(use.get("names")))
        for s in sorted((ran | named) - set(skills)):
            problems.append(f"flow.uses.{rid}: `{s}` is not a skill of this plugin")
        if src is None:
            continue
        path, body = src
        pre = _preloaded(bundle / path)
        found = {s: _first_line(body, re.compile(rf"(?<![\w-]){re.escape(s)}(?![\w-])"))
                 for s in skills if s != rid}
        for s in sorted(loadable):
            if found.get(s) and s not in ran | named | pre:
                problems.append(f"{path}:{found[s]} names `{s}`, which flow.uses.{rid} does not place "
                                f"(always, sometimes, or names)")
        for s in sorted((ran | named) & set(skills)):
            if not found.get(s):
                problems.append(f"flow.uses.{rid} lists `{s}`, which {path} never names")

    # Documents.
    unchecked = 0
    for d in flow.get("documents") or []:
        name, match = d.get("name", "?"), d.get("match", d.get("path"))
        touch = set(_actors(d.get("writes"))) | set(_actors(d.get("reads")))
        named = set(_actors(d.get("names")))
        if match is False or not match:
            unchecked += 1
            continue
        given = "match" in d
        tokens = [str(t) for t in match] if isinstance(match, list) else [str(match)]
        pattern = re.compile("|".join(f"(?:{_mention(t, literal=given).pattern})" for t in tokens))
        for rid in sorted(named - set(roles)):
            problems.append(f"flow.documents `{name}`: names lists `{rid}`, which is not a role")
        for rid, src in roles.items():
            if src is None:
                continue
            path, body = src
            line = _first_line(body, pattern)
            listed = rid in touch or "all" in touch
            if line and not listed and rid not in named and rid not in relays:
                problems.append(f"{path}:{line} names `{name}`, and {rid} is not in its writes, reads or names")
            if not line and (rid in touch or rid in named):
                problems.append(f"flow.documents `{name}` lists {rid}, and {path} never names it "
                                f"(by {', '.join(tokens)})")

    # Drivers and hooks.
    scripts = {x.name for g in ("scripts/*.py", "skills/*/scripts/*.py", "hooks/*.py") for x in bundle.glob(g)}
    hook_scripts = {x.name for x in bundle.glob("hooks/*.py")}
    wired: dict[str, set[str]] = {}
    hooks_file = bundle / "hooks" / "hooks.json"
    if hooks_file.exists():
        for event, groups in (json.loads(hooks_file.read_text()).get("hooks") or {}).items():
            for group in groups:
                for h in group.get("hooks") or []:
                    for word in re.findall(r"[\w-]+\.py", " ".join([h.get("command", "")] + list(h.get("args") or []))):
                        wired.setdefault(word, set()).add(event)
    held_all: set[str] = set()
    for d in flow.get("drivers") or []:
        sid = str(d.get("skill"))
        if sid not in skills:
            problems.append(f"flow.drivers: `{sid}` is not a skill of this plugin")
            continue
        body = skills[sid].read_text()
        for key in ("ledger", "next", "writer", "held", "spawns", "returns"):
            for word in re.findall(r"[\w-]+\.py", str(d.get(key, ""))):
                if word not in scripts:
                    problems.append(f"flow.drivers.{sid}.{key}: `{word}` is not a script or hook of this plugin")
                elif key in ("next", "writer") and word not in body:
                    problems.append(f"flow.drivers.{sid}.{key}: skills/{sid}/SKILL.md never names `{word}`")
        held = set(re.findall(r"[\w-]+\.py", str(d.get("held", ""))))
        held_all |= held
        for word in sorted(held & hook_scripts):
            if word not in wired:
                problems.append(f"flow.drivers.{sid}.held: `{word}` is not wired in hooks/hooks.json")
            else:
                for event in re.findall(r"`([A-Z][A-Za-z]+)`", str(d.get("held", ""))):
                    if event in {"PreToolUse", "PostToolUse", "Stop", "SubagentStop", "SubagentStart",
                                 "SessionStart", "SessionEnd", "UserPromptSubmit", "PreCompact", "Notification"} \
                            and not any(event in wired[w] for w in held if w in wired):
                        problems.append(f"flow.drivers.{sid}.held: no hook named there is wired to `{event}`")
    for word in sorted(set(wired) - held_all):
        problems.append(f"hooks/hooks.json wires `{word}`, which no driver's `held` names")

    if problems:
        return False, f"{len(problems)} disagreement(s):\n      " + "\n      ".join(problems)
    n = len(flow.get("documents") or [])
    return True, (f"{len(roles)} roles, {n} documents ({unchecked} unchecked), "
                  f"{len(flow.get('drivers') or [])} drivers, {len(wired)} hooks")


CHECKS = {"forbid": check_forbid, "headings": check_headings, "names_listed": check_names_listed,
          "flow": check_flow,
          "frontmatter": check_frontmatter}


def main() -> int:
    args = [a for a in sys.argv[1:] if not a.startswith("-")]
    if "--help" in sys.argv or "-h" in sys.argv:
        print(__doc__)
        return 0
    quiet = "--quiet" in sys.argv
    bundle = Path(args[0] if args else ".").resolve()
    config = bundle / "contracts.yml"
    if not config.exists():
        print(f"no contracts.yml in {bundle.name} — nothing declared to check")
        return 2
    try:
        import yaml
    except ImportError:
        sys.exit("contracts.yml needs PyYAML — `pip install pyyaml`.")
    declared = yaml.safe_load(config.read_text()) or {}

    rows = []
    for kind, specs in declared.items():
        if kind not in CHECKS:
            rows.append((f"[{kind}]", "ERROR", f"unknown check kind; known: {', '.join(CHECKS)}"))
            continue
        for spec in specs:
            try:
                ok, detail = CHECKS[kind](bundle, spec)
            except (LookupError, OSError) as e:
                ok, detail = False, f"could not run: {e}"
            rows.append((spec.get("name", kind), "PASS" if ok else "FAIL", detail))

    if not rows:
        print("contracts.yml declares no checks")
        return 2
    width = max(len(r[0]) for r in rows)
    for name, verdict, detail in rows:
        if verdict != "PASS" or not quiet:
            print(f"{verdict}  {name:<{width}}  {detail}")
    failed = [r for r in rows if r[1] != "PASS"]
    print(f"\n{len(rows) - len(failed)}/{len(rows)} pass")
    return 1 if failed else 0


if __name__ == "__main__":
    sys.exit(main())
