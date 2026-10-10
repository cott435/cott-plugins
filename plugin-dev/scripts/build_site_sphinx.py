"""Render a Claude Code plugin bundle as a Sphinx (MyST + Furo) site for reading.

Usage:  python3 build_site_sphinx.py [bundle] [--evals evals.json] [--build]

Same discovery as build_site.py — agents, commands, skills and their references, rules, the
README, and everything authored under `site/` — with two differences that are the point of
this builder:

  * a skill is a page with its `references/` as children (a toctree), not a flat list;
  * scripts are pages: each `scripts/*.py` (and `skills/*/scripts/*.py`) is rendered from its
    module docstring, its argparse help (every subcommand), its public functions and its
    source, and every backticked mention of it in a skill, agent or workflow becomes a link
    to that page, which lists what links back.

Relative `.md` links between pages are rewritten to the generated layout, so a link that
works on GitHub works here; one that resolves to a file the site does not render is left
alone and Sphinx reports it.

Writes, all generated and safe to gitignore:

    <bundle>/site/sphinx/   MyST sources, conf.py, one index.md with the toctrees
    <bundle>/site/_build/   HTML, with --build (needs sphinx, myst-parser, furo,
                            sphinxcontrib-mermaid)

Authored inputs are the ones build_site.py reads (`site/site.yml`, `flow.md`, `workflows/`,
`notes/`, `extra.css`); there is nothing new to write.
"""

from __future__ import annotations

import argparse
import ast
import importlib.util
import json
import os
import re
import shutil
import subprocess
import sys
import tempfile
from pathlib import Path

KIT = Path(__file__).resolve().parent
sys.path.insert(0, str(KIT))
from build_site import (DEFAULTS, fm_table, load_config, ordered,  # noqa: E402
                        plugin_name, split_frontmatter)

LINK = re.compile(r"(?<!\!)\]\(([^)#\s]+\.md)(#[^)\s]*)?\)")
FENCE = re.compile(r"^\s*(```+|~~~+)")
SKIP_LINE = re.compile(r"^\s*(\[|\||#)")   # keep headings, tables and refs free of injected links


def demote(body: str) -> str:
    """Shift headings so the shallowest one in the body is H2 (the page title is the H1).
    Sphinx warns on a skipped level, so a body that starts at `##` is left as it is."""
    levels, in_fence = [], False
    for line in body.split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := re.match(r"^(#{1,6}) ", line)):
            levels.append(len(m.group(1)))
    if not levels or min(levels) >= 2:
        return body
    by, in_fence, out = 2 - min(levels), False, []
    for line in body.split("\n"):
        if FENCE.match(line):
            in_fence = not in_fence
        elif not in_fence and (m := re.match(r"^(#{1,6}) ", line)):
            line = "#" * min(6, len(m.group(1)) + by) + line[len(m.group(1)):]
        out.append(line)
    return "\n".join(out)


class Page:
    """One generated page: where it came from, where it goes, and its text."""

    def __init__(self, rel: str, title: str, text: str, src: Path | None = None):
        self.rel, self.title, self.text, self.src = rel, title, text, src
        self.children: list[Page] = []     # rendered as this page's toctree
        self.linked_from: list[Page] = []  # scripts only: who mentions it


def head(title: str, source: str, fm: dict[str, str] | None = None) -> str:
    return f"# {title}\n\n*Source: `{source}`*\n\n{fm_table(fm or {})}"


# --------------------------------------------------------------------------- scripts

class _Captured(Exception):
    def __init__(self, parser):
        self.parser = parser


def _capture_here(path: Path):
    """Import a script and run its main() until it asks argparse to parse, then return the
    parser. Only ever called in the child process of capture_parser."""
    import argparse as ap

    def grab(self, *a, **k):
        raise _Captured(self)

    ap.ArgumentParser.parse_args = grab
    ap.ArgumentParser.parse_known_args = grab
    spec = importlib.util.spec_from_file_location(f"_site_{path.stem}", path)
    sys.argv = [path.name]
    mod = importlib.util.module_from_spec(spec)
    sys.modules[spec.name] = mod
    spec.loader.exec_module(mod)
    try:
        mod.main()
    except _Captured as c:
        return c.parser
    return None


def capture_parser(path: Path) -> list[tuple[str, str]]:
    """[(command line, help text)] for a script: its argparse parser and every subcommand.

    Runs in a child process in an empty directory, so a main() that does work before it
    parses arguments can neither write into the repo nor stall this build. A script that
    never hands argparse a parse falls back to the text of its own `--help`."""
    with tempfile.TemporaryDirectory() as tmp:
        try:
            r = subprocess.run([sys.executable, str(Path(__file__).resolve()), "--capture", str(path)],
                               cwd=tmp, capture_output=True, text=True, timeout=30)
            got = json.loads(r.stdout.strip().splitlines()[-1]) if r.returncode == 0 and r.stdout.strip() else []
        except (subprocess.TimeoutExpired, ValueError):
            got = []
        if got:
            return [tuple(x) for x in got]
        try:
            r = subprocess.run([sys.executable, str(path), "--help"], cwd=tmp,
                               capture_output=True, text=True, timeout=30)
        except subprocess.TimeoutExpired:
            return []
        return [(f"python3 {path.name} --help", r.stdout.rstrip())] if r.returncode == 0 and r.stdout.strip() else []


def parser_help(parser, prog: str) -> list[tuple[str, str]]:
    """[(command line, help text)] for the parser and, recursively, each subcommand."""
    parser.prog = prog
    out = [(prog, parser.format_help().rstrip())]
    for action in parser._actions:
        if isinstance(action, argparse._SubParsersAction):
            for name, sub in action.choices.items():
                out += parser_help(sub, f"{prog} {name}")
    return out


def script_page(path: Path, bundle: Path, rel: str) -> Page:
    src = path.read_text()
    tree = ast.parse(src)
    doc = ast.get_docstring(tree) or "(no module docstring)"
    relsrc = path.relative_to(bundle).as_posix()
    lines = [f"# {relsrc}\n"]
    lines.append(f"## Overview\n\n````text\n{doc}\n````\n")

    commands = capture_parser(path)
    if commands:
        lines.append("## Commands\n")
        for prog, text in commands:
            lines.append(f"### `{prog}`\n\n```text\n{text}\n```\n")

    funcs = []
    for node in tree.body:
        if isinstance(node, (ast.FunctionDef, ast.ClassDef)) and not node.name.startswith("_"):
            d = (ast.get_docstring(node) or "").strip().split("\n\n")[0].replace("\n", " ")
            kind = "class" if isinstance(node, ast.ClassDef) else "def"
            funcs.append(f"| `{kind} {node.name}` | {d.replace('|', chr(92) + '|') or '—'} |")
    if funcs:
        lines.append("## Functions\n\n| name | what it does |\n|---|---|\n" + "\n".join(funcs) + "\n")

    lines.append("@@LINKED_FROM@@")
    lines.append(f"## Source\n\n```{{literalinclude}} @@SRC@@\n:language: python\n:linenos:\n```\n")
    p = Page(rel, relsrc, "\n".join(lines), path)
    return p


# --------------------------------------------------------------------------- build

def relpath(frm: str, to: str) -> str:
    """Relative link from page `frm` to page `to` (both site-relative, posix)."""
    a, b = Path(frm).parent.parts, Path(to).parts
    i = 0
    while i < len(a) and i < len(b) - 1 and a[i] == b[i]:
        i += 1
    return "/".join([".."] * (len(a) - i) + list(b[i:]))


def main() -> None:
    if len(sys.argv) == 3 and sys.argv[1] == "--capture":      # child of capture_parser
        target = Path(sys.argv[2])
        parser = _capture_here(target)
        if parser is not None:
            print(json.dumps(parser_help(parser, f"python3 {target.name}")))
        return
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", nargs="?", default=".")
    ap.add_argument("--evals", default=None)
    ap.add_argument("--build", action="store_true", help="also run sphinx-build into site/_build")
    args = ap.parse_args()

    bundle = Path(args.bundle).resolve()
    name = plugin_name(bundle)
    site = bundle / "site"
    out = site / "sphinx"
    cfg = load_config(site)
    title = cfg.get("site_title", name)
    prefix = cfg.get("command_prefix", name)

    if out.exists():
        shutil.rmtree(out)
    out.mkdir(parents=True)

    pages: list[Page] = []
    by_src: dict[Path, Page] = {}

    def add(page: Page, src: Path | None = None) -> Page:
        pages.append(page)
        if src is not None:
            by_src[src.resolve()] = page
        return page

    # Home and orientation
    home = None
    readme = bundle / "README.md"
    if readme.exists():
        body = re.sub(r"^# .*\n", "", readme.read_text(), count=1)
        home = add(Page("readme.md", "Home (README)",
                        f"# {title}\n\n*Source: `README.md`*\n\n{demote(body)}", readme), readme)
    flow = site / "flow.md"
    flow_page = add(Page("flow.md", "The flow", flow.read_text(), flow), flow) if flow.exists() else None

    # Workflows
    workflows: list[Page] = []
    wf_dir = site / "workflows"
    if wf_dir.exists():
        files = {p.stem: p for p in wf_dir.glob("*.md")}
        for stem in ordered(files, cfg.get("workflows_order") or []):
            p = files[stem]
            text = p.read_text()
            h1 = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), stem)
            workflows.append(add(Page(f"workflows/{p.name}", h1, text, p), p))

    # Agents and commands
    agents, commands = [], []
    for p in sorted((bundle / "agents").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        agents.append(add(Page(f"agents/{p.stem}.md", p.stem,
                               head(f"agent: {p.stem}", f"agents/{p.name}", fm) + demote(body), p), p))
    for p in sorted((bundle / "commands").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        commands.append(add(Page(f"commands/{p.stem}.md", f"/{prefix}:{p.stem}",
                                 head(f"/{prefix}:{p.stem}", f"commands/{p.name}", fm) + demote(body), p), p))

    # Skills: SKILL.md is the page, references/ are its children.
    wf_skills: dict[str, Page] = {}
    knowledge: list[Page] = []
    for p in sorted((bundle / "skills").glob("*/SKILL.md")):
        fm, body = split_frontmatter(p.read_text())
        skill = p.parent.name
        user_run = (fm.get("context") == "fork"
                    or str(fm.get("disable-model-invocation", "")).strip().lower() == "true")
        stitle = f"/{prefix}:{skill}" if user_run else skill
        body = body.replace("](references/", "](")     # refs sit beside the skill page
        page = add(Page(f"skills/{skill}/index.md", stitle,
                        head(stitle, f"skills/{skill}/SKILL.md", fm) + demote(body), p), p)
        refs = p.parent / "references"
        for r in sorted(refs.glob("*.md")) if refs.exists() else []:
            page.children.append(add(Page(
                f"skills/{skill}/{r.stem}.md", r.stem,
                head(f"{skill} / {r.stem}", f"skills/{skill}/references/{r.name}") + demote(r.read_text()),
                r), r))
        (wf_skills.__setitem__(skill, page) if user_run else knowledge.append(page))
    wf_pages = [wf_skills[n] for n in ordered(wf_skills, cfg.get("workflow_skills_order") or [])]

    # Scripts
    scripts: list[Page] = []
    found = sorted((bundle / "scripts").glob("*.py")) + sorted((bundle / "skills").glob("*/scripts/*.py"))
    taken: set[str] = set()
    for p in found:
        slug = p.stem if p.stem not in taken else f"{p.parent.parent.name}-{p.stem}"
        taken.add(p.stem)
        scripts.append(add(script_page(p, bundle, f"scripts/{slug}.md"), p))
    script_by_name = {s.src.name: s for s in scripts}

    # Rules and config
    rules_config: list[Page] = []
    for p in sorted((bundle / "rules").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        rules_config.append(add(Page(f"rules/{p.name}", f"rule {p.stem}",
                                     head(f"rule: {p.stem}", f"rules/{p.name}", fm) + demote(body), p), p))
    for rel in cfg.get("config_files") or []:
        p = bundle / rel
        if p.exists():
            lang = p.suffix.lstrip(".") or "text"
            rules_config.append(add(Page(
                f"config/{p.stem}.md", p.name,
                f"# {p.name}\n\n*Source: `{rel}`*\n\n````{lang}\n{p.read_text()}\n````\n", p)))
        else:
            print(f"  ! config_files lists {rel}, which does not exist — skipped")

    # Notes: loose files, and each plan folder's overview only.
    notes: list[Page] = []
    nd = site / "notes"
    if nd.exists():
        for n in sorted(nd.glob("*.md")):
            notes.append(add(Page(f"notes/{n.name}", n.stem.replace("-", " "), n.read_text(), n), n))
        for plan in sorted(d for d in nd.iterdir() if d.is_dir()):
            for n in sorted(plan.glob("*-00-overview.md")):
                notes.append(add(Page(f"notes/{plan.name}-{n.name}", f"{plan.name} overview",
                                      n.read_text(), n), n))

    evals_page = None
    if args.evals:
        data = json.loads(Path(args.evals).read_text())
        lines = ["# Eval definitions\n", f"*Source: `{Path(args.evals).name}`*\n", f"\n{data.get('notes', '')}\n"]
        for e in data["evals"]:
            lines.append(f"\n## {e['id']} — {e['name']}\n\n**Invocation:** `{e['invocation']}`  \n"
                         f"**Fixture:** {e['fixture']}\n\n**Prompt:** {e['prompt']}\n\n"
                         f"**Expected:** {e['expected_output']}\n")
        evals_page = add(Page("evals.md", "Evals", "\n".join(lines)))

    # ---- link pass: script mentions become links, relative .md links follow the layout.
    mention = re.compile(r"`([^`\n]*?(?<![\w-])(" + "|".join(re.escape(n) for n in script_by_name)
                   + r")(?![\w-])[^`\n]*)`") \
        if script_by_name else None
    for page in pages:
        if page.src is None or page.src.suffix != ".md":
            continue
        in_fence, lines = False, []
        for line in page.text.split("\n"):
            if FENCE.match(line):
                in_fence = not in_fence
            if not in_fence and not SKIP_LINE.match(line) and mention:
                def sub(m, page=page):
                    target = script_by_name[m.group(2)]
                    if page is not target and page not in target.linked_from:
                        target.linked_from.append(page)
                    return f"[`{m.group(1)}`]({relpath(page.rel, target.rel)})"
                line = mention.sub(sub, line)
            lines.append(line)
        text = "\n".join(lines)

        def fix(m, page=page):
            hit = by_src.get((page.src.parent / m.group(1)).resolve())
            if hit is None:
                return m.group(0)
            return f"]({relpath(page.rel, hit.rel)}{m.group(2) or ''})"
        page.text = LINK.sub(fix, text)

    for s in scripts:
        links = ""
        if s.linked_from:
            links = "## Referenced by\n\n" + "\n".join(
                f"- [{p.title}]({relpath(s.rel, p.rel)})" for p in s.linked_from) + "\n\n"
        s.text = s.text.replace("@@LINKED_FROM@@", links) \
                       .replace("@@SRC@@", os.path.relpath(s.src, (out / s.rel).parent))

    # ---- write
    for page in pages:
        text = page.text
        if page.children:
            entries = "\n".join(f"{c.title} <{Path(c.rel).name}>" for c in page.children)
            text += f"\n\n```{{toctree}}\n:hidden:\n:caption: References\n\n{entries}\n```\n"
        dest = out / page.rel
        dest.parent.mkdir(parents=True, exist_ok=True)
        dest.write_text(text)

    def toc(caption: str, group: list[Page]) -> str:
        if not group:
            return ""
        entries = "\n".join(f"{p.title} <{p.rel}>" for p in group)
        return f"```{{toctree}}\n:caption: {caption}\n:maxdepth: 1\n\n{entries}\n```\n\n"

    top = [p for p in (home, flow_page) if p]
    index = f"# {title}\n\nReading site for the `{name}` plugin.\n\n" + toc("Start", top) \
        + toc("Workflows", workflows) + toc("Agents", agents) + toc("Commands", commands) \
        + toc("Workflow skills", wf_pages) + toc("Knowledge skills", knowledge) \
        + toc("Scripts", scripts) + toc("Rules and config", rules_config) \
        + toc("Notes", notes) + toc("Evals", [evals_page] if evals_page else [])
    (out / "index.md").write_text(index)

    css = site / "extra.css"
    (out / "_static").mkdir()
    (out / "_static" / "extra.css").write_text(
        (css if css.exists() else DEFAULTS / "extra.css").read_text()
        .replace(".md-typeset ", ""))     # the Material selectors; Furo has no .md-typeset
    (out / "conf.py").write_text(CONF.format(title=title.replace("'", "\\'"), name=name))

    print(f"{name}: wrote {len(pages) + 1} pages under {out}")
    print(f"  {len(agents)} agents, {len(commands)} commands, {len(workflows)} workflows, "
          f"{len(wf_pages)} workflow skills, {len(knowledge)} knowledge skills, "
          f"{len(scripts)} scripts, {len(rules_config)} rules/config, {len(notes)} notes")

    if args.build:
        build = site / "_build"
        r = subprocess.run([sys.executable, "-m", "sphinx", "-b", "html", "-q", str(out), str(build)])
        print(f"  html -> {build}/index.html" if r.returncode == 0 else "  ! sphinx-build failed")
        sys.exit(r.returncode)
    print(f"  build -> python3 -m sphinx -b html {out} {site / '_build'}")


CONF = """\
# Generated by plugin-dev's build_site_sphinx.py — do not edit; rebuilt on every run.
project = '{title}'
extensions = ['myst_parser', 'sphinxcontrib.mermaid']
source_suffix = {{'.md': 'markdown'}}
exclude_patterns = ['_build']
myst_enable_extensions = ['colon_fence', 'deflist']
myst_heading_anchors = 3
myst_fence_as_directive = ['mermaid']
html_theme = 'furo'
html_title = '{title}'
html_static_path = ['_static']
html_css_files = ['extra.css']
html_theme_options = {{
    'light_css_variables': {{'color-brand-primary': '#00897b', 'color-brand-content': '#00897b'}},
    'dark_css_variables': {{'color-brand-primary': '#4db6ac', 'color-brand-content': '#4db6ac'}},
}}
"""


if __name__ == "__main__":
    main()
