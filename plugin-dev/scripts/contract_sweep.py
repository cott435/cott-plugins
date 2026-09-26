#!/usr/bin/env python3
"""Check the cross-file claims a plugin's agents act on and nothing else verifies.

A plugin is a set of prompts that reference each other by name: one agent owns a document
template, others parse it by heading; one skill forbids something another still describes.
Nothing fails when those drift — the agent just reads for a heading that is never written.
This runner checks the claims a bundle declares in its own `contracts.yml`.

Four kinds of claim, all of them about file contents, so all of them decidable without
running a model:

  forbid        a pattern that must not appear (a rule one file states and another breaks),
                its exemptions scoped to the whole line or, with <near>, to each match
  headings      every heading a reader parses is one the owner's template defines, read from
                its numbered **bold** items or, with <owner_form: markdown>, its `##` headings
  names_listed  every directory under <dirs> has its name in <file> (a list that goes stale),
                narrowed by <where> on frontmatter and read in one of three <form>s
  frontmatter   every frontmatter key in <files> is one plugin-anatomy documents for <kind>
                (skill or agent), and none is a key plugins ignore

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


CHECKS = {"forbid": check_forbid, "headings": check_headings, "names_listed": check_names_listed,
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
        sys.exit("contracts.yml needs PyYAML — `pip install pyyaml` (mkdocs pulls it in).")
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
