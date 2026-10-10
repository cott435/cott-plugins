"""Render a Claude Code plugin bundle as a Sphinx (MyST + Furo) site for reading.

Usage:  python3 build_site.py [bundle] [--evals evals.json] [--build]

Everything the site shows is discovered from the bundle: every agent, command, skill (plus
its `references/`), rule, script, the README, and any authored page under `site/`. Nothing
here is specific to one plugin; the only per-plugin knobs live in `site/site.yml`, and every
one of them is optional. Two things set this site apart from a flat list of pages:

  * a skill is a page with its `references/` as children (a toctree), not a flat list;
  * scripts are pages: each `scripts/*.py` (and `skills/*/scripts/*.py`) is rendered from its
    module docstring, its argparse help (every subcommand), its public functions and its
    source, and every backticked mention of it in a skill, agent or workflow becomes a link
    to that page, which lists what links back.

Relative `.md` links between pages are rewritten to the generated layout, so a link that
works on GitHub works here; one that resolves to a file the site does not render is left
alone and Sphinx reports it.

Writes, all generated and safe to gitignore:

    <bundle>/site/docs/     MyST sources, conf.py, one index.md with the toctrees
    <bundle>/site/_build/   HTML, with --build (needs sphinx, myst-parser, furo,
                            sphinxcontrib-mermaid)

Authored, and committed, in the consuming repo: `site/site.yml`, `site/flow.md`,
`site/workflows/*.md`, `site/reference/*.md`, `site/notes/*.md` (and `site/notes/<slug>/`,
of which only `<slug>-00-overview.md` is rendered) and an optional `site/extra.css`.

The flow page has the same parts in every plugin. `site/flow.md` holds the prose and one
marker line per generated part, and this script fills each from the bundle and the `flow:`
block of `site/site.yml`:

    <!-- flow:agents-skills -->   which role uses which skill: always, or on a condition
    <!-- flow:writes -->          the roles in a row, the documents each alone writes above
                                  it, the documents several write below it
    <!-- flow:reads -->           the same chart for what each role reads
    <!-- flow:documents -->       the table behind both charts
    <!-- flow:drivers -->         each driver, what tells it the next step, its ledger

A plugin with agents and no `site/flow.md` gets a flow page of just those parts.

Nav shape (a section is omitted entirely when it has nothing in it):

    Start (README, the flow) -> Workflows -> Reference -> Agents -> Commands ->
    Workflow skills -> Knowledge skills -> Scripts -> Rules and config -> Notes -> Evals
"""

from __future__ import annotations

import argparse
import ast
import html
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
DEFAULTS = KIT / "defaults"
FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


# --------------------------------------------------------------------------- bundle

def split_frontmatter(text: str) -> tuple[dict[str, str], str]:
    """Return (frontmatter as ordered dict of raw strings, body)."""
    m = FM_RE.match(text)
    if not m:
        return {}, text
    fm: dict[str, str] = {}
    key = None
    for line in m.group(1).splitlines():
        if re.match(r"^\s+- ", line) and key:
            fm[key] = (fm[key] + ", " if fm[key] else "") + line.strip()[2:].strip()
            continue
        mm = re.match(r"^([\w-]+):\s*(.*)$", line)
        if mm:
            key = mm.group(1)
            fm[key] = mm.group(2).strip()
    return fm, text[m.end():]


def load_config(site: Path) -> dict:
    """Read site/site.yml if present. Absent or empty is a valid, fully defaulted config."""
    path = site / "site.yml"
    if not path.exists():
        return {}
    try:
        import yaml
    except ImportError:
        sys.exit(f"{path} exists but PyYAML is not installed — `pip install pyyaml` "
                 f"or delete the file to use defaults.")
    return yaml.safe_load(path.read_text()) or {}


def plugin_name(bundle: Path) -> str:
    manifest = bundle / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        sys.exit(f"no .claude-plugin/plugin.json under {bundle} — is that a plugin repo? "
                 f"(pass the repo root as the first argument)")
    return json.loads(manifest.read_text())["name"]


def fm_table(fm: dict[str, str]) -> str:
    """Render frontmatter as a two-column table so it is visible in the site."""
    if not fm:
        return ""
    pipe = "\\|"
    rows = "\n".join(f"| `{k}` | {v.replace('|', pipe) or '—'} |" for k, v in fm.items())
    return f"| frontmatter | value |\n|---|---|\n{rows}\n\n"


def ordered(names, preferred: list[str]):
    """`preferred` first in the order given, then everything else alphabetically."""
    listed = [n for n in preferred if n in names]
    return listed + sorted(n for n in names if n not in preferred)


# --------------------------------------------------------------------------- pages

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


# --------------------------------------------------------------------------- the flow page

FLOW_MARK = re.compile(r"^[ \t]*<!--\s*flow:([a-z-]+)\s*-->[ \t]*$", re.M)
FLOW_PARTS = ("agents-skills", "writes", "reads", "documents", "drivers")
DEFAULT_FLOW = """# The flow

## Agents and skills

<!-- flow:agents-skills -->

## Who writes what

<!-- flow:writes -->

## Who reads what

<!-- flow:reads -->

<!-- flow:documents -->

## How the drivers run

<!-- flow:drivers -->
"""
PALETTE = ["#00897b", "#1e88e5", "#8e5bd0", "#d23f7a", "#e07b1a", "#7a9a1e", "#1aa3b8", "#d9463d"]
CHART_CSS = (
    ".df-role{fill:var(--color-background-secondary,#f8f9fb);stroke-width:2}"
    ".df-doc{fill:var(--color-background-primary,#fff);stroke:var(--color-foreground-border,#878787)}"
    ".df-sep{stroke:var(--color-background-border,#ddd)}"
    ".df-t{font:600 11.5px sans-serif;fill:var(--color-foreground-primary,#000);text-anchor:middle}"
    ".df-n{font:9.5px sans-serif;fill:var(--color-foreground-muted,#646776);text-anchor:middle}"
    ".df-d{font:10.5px sans-serif;fill:var(--color-foreground-primary,#000);text-anchor:middle}"
    ".df-e{fill:none;stroke-width:1.4;opacity:.9}"
    ".docflow a,.driverflow a{text-decoration:none}"
)
# A chart wider than the text column takes the room to the window's right edge before it scrolls.
CHART_FIT = (
    "(function(){function fit(){document.querySelectorAll('.docflow').forEach(function(d){"
    "d.style.width='';var r=d.getBoundingClientRect(),need=+d.firstElementChild.getAttribute('width'),"
    "room=document.documentElement.clientWidth-r.left-16;"
    "if(need>r.width&&room>r.width)d.style.width=Math.min(need,room)+'px';});}"
    "if(!window.docflowFit){window.docflowFit=fit;addEventListener('resize',fit);}fit();})();"
)


class Role:
    """One actor on the flow page: an agent, a skill, or a name site.yml gives a label."""

    def __init__(self, rid: str, label: str, note: str, rel: str | None):
        self.id, self.label, self.note, self.rel = rid, label, note, rel


def actors(value) -> list[tuple[str, str]]:
    """[(name, note)] from a name, a list of names, or `{name: note}` mappings in either."""
    if not value:
        return []
    out: list[tuple[str, str]] = []
    for v in value if isinstance(value, list) else [value]:
        if isinstance(v, dict):
            out += [(str(k), str(n or "")) for k, n in v.items()]
        else:
            out.append((str(v), ""))
    return out


def flow_roles(flow: dict, agents: dict[str, Page], skills: dict[str, tuple[Page, bool]]) -> list[Role]:
    """The flow page's roles, left to right: `flow.roles` when site.yml lists them, otherwise
    every agent. A name that is an agent or a skill links to its page."""
    def make(entry) -> Role:
        e = entry if isinstance(entry, dict) else {"id": entry}
        rid = str(e["id"])
        if rid in agents:
            page, note = agents[rid], "agent"
        elif rid in skills:
            page, note = skills[rid][0], "typed skill" if skills[rid][1] else "skill"
        else:
            page, note = None, ""
        return Role(rid, str(e.get("label", rid)), str(e.get("note", note)), page.rel if page else None)
    return [make(e) for e in flow.get("roles") or list(agents)]


def cell(text) -> str:
    return str(text).replace("|", "\\|").replace("\n", " ")


def linked(label: str, rel: str | None) -> str:
    return f"[{label}]({rel})" if rel else label


def uses_table(roles: list[Role], flow: dict, preloaded: dict[str, list[str]],
               skills: dict[str, tuple[Page, bool]]) -> str:
    """Which role uses which skill. A skill in an agent's `skills:` frontmatter is always
    used; `flow.uses.<role>.always` and `.sometimes` in site.yml add the ones a body invokes."""
    marks: dict[tuple[str, str], str] = {}
    when: list[tuple[Role, str, str]] = []
    for r in roles:
        use = (flow.get("uses") or {}).get(r.id) or {}
        for s, why in actors(use.get("sometimes")):
            marks[(r.id, s)] = "○"
            if why:
                when.append((r, s, why))
        for s in preloaded.get(r.id, []) + [s for s, _ in actors(use.get("always"))]:
            marks[(r.id, s)] = "●"
    if not marks:
        return "*No role here uses a skill.*\n"
    used = [r for r in roles if any(k[0] == r.id for k in marks)]
    names = sorted({k[1] for k in marks})

    def skill(s: str) -> str:
        return linked(f"`{s}`", skills[s][0].rel if s in skills else None)

    across = sum(len(r.label) for r in used) <= sum(len(s) for s in names)
    cols = [linked(r.label, r.rel) for r in used] if across else [skill(s) for s in names]
    lines = ["| | " + " | ".join(cols) + " |", "|---|" + ":-:|" * len(cols)]
    if across:
        lines += [f"| {skill(s)} | " + " | ".join(marks.get((r.id, s), "") for r in used) + " |" for s in names]
    else:
        lines += [f"| {linked(r.label, r.rel)} | " + " | ".join(marks.get((r.id, s), "") for s in names) + " |"
                  for r in used]
    out = "\n".join(lines) + "\n\n● always: preloaded by the agent's `skills:` frontmatter, or run every time. " \
                             "○ only on a condition.\n"
    if when:
        out += "\n| | Uses | When |\n|---|---|---|\n" + "\n".join(
            f"| {linked(r.label, r.rel)} | {skill(s)} | {cell(why)} |" for r, s, why in when) + "\n"
    idle = [linked(r.label, r.rel) for r in roles if r not in used]
    if idle:
        out += "\nNo skill: " + ", ".join(idle) + ".\n"
    return out


def wrap(text: str, width: int) -> list[str]:
    lines, cur = [], ""
    for word in str(text).split():
        if cur and len(cur) + 1 + len(word) > width:
            lines.append(cur)
            cur = word
        else:
            cur = f"{cur} {word}".strip()
    return lines + [cur] if cur or not lines else lines


def doc_chart(roles: list[Role], docs: list[dict], mode: str) -> tuple[str, list[dict]]:
    """One document chart, as inline SVG, and the documents every role touches.

    The roles sit in one row. Above each is the list of documents only it writes (`mode`
    "writes") or only it reads ("reads"); below the row are the documents several roles
    share, each joined to its roles by an arrow that points the way the content moves. A
    document marked `all` is returned for the caption instead of drawn."""
    esc = html.escape
    own: dict[str, list[dict]] = {r.id: [] for r in roles}
    shared: list[tuple[dict, list[str]]] = []
    everyone: list[dict] = []
    for d in docs:
        named = list(dict.fromkeys(a for a, _ in actors(d.get(mode))))
        if "all" in named:
            everyone.append(d)
            continue
        hit = [a for a in named if a in own]
        if len(hit) == 1:
            own[hit[0]].append(d)
        elif hit:
            shared.append((d, hit))
    shown = [r for r in roles if own[r.id] or any(r.id in hit for _, hit in shared)]
    if not shown:
        return "", everyone

    cw, gx, pad, lh, role_h, sw = 108, 8, 10, 13, 36, 128
    width = pad * 2 + len(shown) * (cw + gx) - gx
    left = {r.id: pad + i * (cw + gx) for i, r in enumerate(shown)}
    cx = {rid: x + cw / 2 for rid, x in left.items()}
    colour = {r.id: PALETTE[i % len(PALETTE)] for i, r in enumerate(shown)}
    uid = f"df{mode[0]}"

    stacks = {rid: [wrap(d["name"], 17) for d in ds] for rid, ds in own.items() if ds}
    stack_h = {rid: 12 + sum(len(ls) * lh for ls in blocks) + 9 * (len(blocks) - 1)
               for rid, blocks in stacks.items()}
    top = max(stack_h.values(), default=0)
    y_role = pad + top + 24 if top else pad
    y_low = y_role + role_h

    # Shared documents: each under the mean of its roles, the most shared first so they sit
    # nearest the row; one that finds no free place close enough starts a row further down.
    placed: list[tuple[dict, list[str], float, int, list[str]]] = []
    rows: list[list[tuple[float, float]]] = []
    for d, hit in sorted(shared, key=lambda t: (-len(t[1]), sum(cx[h] for h in t[1]) / len(t[1]), t[0]["name"])):
        lo, hi = pad, max(pad, width - pad - sw)
        want = min(max(sum(cx[h] for h in hit) / len(hit) - sw / 2, lo), hi)
        for n, taken in enumerate(rows):
            spots = [want] + [a - sw - 10 for a, _ in taken] + [b + 10 for _, b in taken]
            free = [x for x in spots if lo <= x <= hi and all(x + sw + 10 <= a or x >= b + 10 for a, b in taken)]
            if free and abs(min(free, key=lambda x: abs(x - want)) - want) <= sw * 1.2:
                x = min(free, key=lambda x: abs(x - want))
                break
        else:
            n, x = len(rows), want
            rows.append([])
        rows[n].append((x, x + sw))
        placed.append((d, hit, x, n, wrap(d["name"], 20)))
    row_h = [max((12 + len(ls) * lh for _, _, _, n, ls in placed if n == i), default=0) for i in range(len(rows))]
    row_y, y = [], y_low + 58
    for h in row_h:
        row_y.append(y)
        y += h + 30
    height = (row_y[-1] + row_h[-1] if rows else y_low) + pad

    out = [f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height:.0f}" width="{width}" '
           f'role="img" style="display:block;width:100%;height:auto;min-width:{width * 0.85:.0f}px;'
           f'max-width:{width}px"><style>{CHART_CSS}</style><defs>']
    for rid, c in colour.items():
        out.append(f'<marker id="{uid}-{shown.index(next(r for r in shown if r.id == rid))}" viewBox="0 0 8 8" '
                   f'refX="7" refY="4" markerWidth="7" markerHeight="7" orient="auto">'
                   f'<path d="M0 0L8 4L0 8z" fill="{c}"/></marker>')
    out.append("</defs>")
    index = {r.id: i for i, r in enumerate(shown)}

    def arrow(points: str, rid: str) -> str:
        return (f'<path class="df-e" d="{points}" stroke="{colour[rid]}" '
                f'marker-end="url(#{uid}-{index[rid]})"/>')

    # Arrows first, so a box drawn later hides the part of a line that passes behind it.
    ports_r = {r.id: sorted((x + sw / 2, i) for i, (_, hit, x, _, _) in enumerate(placed) if r.id in hit)
               for r in shown}
    for i, (d, hit, x, n, ls) in enumerate(placed):
        ends = sorted(hit, key=lambda h: cx[h])
        for j, rid in enumerate(ends):
            k = len(ports_r[rid])
            sx = cx[rid] + (ports_r[rid].index((x + sw / 2, i)) - (k - 1) / 2) * min(12, (cw - 30) / max(k - 1, 1))
            ex = x + sw / 2 + (j - (len(ends) - 1) / 2) * min(14, (sw - 30) / max(len(ends) - 1, 1))
            ey, bend = row_y[n], max(26, (row_y[n] - y_low) * 0.45)
            if mode == "writes":
                out.append(arrow(f"M{sx:.1f} {y_low}C{sx:.1f} {y_low + bend:.1f} {ex:.1f} {ey - bend:.1f} {ex:.1f} {ey}", rid))
            else:
                out.append(arrow(f"M{ex:.1f} {ey}C{ex:.1f} {ey - bend:.1f} {sx:.1f} {y_low + bend:.1f} {sx:.1f} {y_low}", rid))
    for rid in stacks:
        a, b = (y_role, pad + top) if mode == "writes" else (pad + top, y_role)
        out.append(arrow(f"M{cx[rid]} {a}L{cx[rid]} {b}", rid))

    def doc_lines(d: dict, lines: list[str], x: float, y: float) -> float:
        out.append(f'<g><title>{esc(str(d.get("path", d["name"])))}</title>')
        for line in lines:
            y += lh
            out.append(f'<text class="df-d" x="{x:.1f}" y="{y:.1f}">{esc(line)}</text>')
        out.append("</g>")
        return y

    for rid, blocks in stacks.items():
        y0 = pad + top - stack_h[rid]
        out.append(f'<rect class="df-doc" x="{left[rid]}" y="{y0}" width="{cw}" height="{stack_h[rid]}" rx="3" '
                   f'style="stroke:{colour[rid]}"/>')
        y = y0 + 2
        for n, (d, lines) in enumerate(zip(own[rid], blocks)):
            if n:
                out.append(f'<line class="df-sep" x1="{left[rid] + 8}" x2="{left[rid] + cw - 8}" '
                           f'y1="{y + 8.5}" y2="{y + 8.5}"/>')
                y += 9
            y = doc_lines(d, lines, cx[rid], y)
    for r in shown:
        box = (f'<rect class="df-role" x="{left[r.id]}" y="{y_role}" width="{cw}" height="{role_h}" rx="6" '
               f'stroke="{colour[r.id]}"/>'
               f'<text class="df-t" x="{cx[r.id]}" y="{y_role + (16 if r.note else 23)}">{esc(r.label)}</text>')
        if r.note:
            box += f'<text class="df-n" x="{cx[r.id]}" y="{y_role + 30}">{esc(r.note)}</text>'
        out.append(f'<a href="{esc(r.rel[:-3])}.html">{box}</a>' if r.rel else box)
    for d, hit, x, n, lines in placed:
        out.append(f'<rect class="df-doc" x="{x:.1f}" y="{row_y[n]}" width="{sw}" '
                   f'height="{12 + len(lines) * lh}" rx="3"/>')
        doc_lines(d, lines, x + sw / 2, row_y[n] + 2)
    out.append("</svg>")
    return ('```{raw} html\n<div class="docflow" style="overflow-x:auto;margin:1em 0;position:relative;'
            'z-index:60;background:var(--color-background-primary,#fff)">\n'
            + "\n".join(out) + f"\n</div>\n<script>{CHART_FIT}</script>\n```\n"), everyone


def chart_section(roles: list[Role], docs: list[dict], mode: str) -> str:
    svg, everyone = doc_chart(roles, docs, mode)
    if not svg and not everyone:
        return ""
    verb = "writes" if mode == "writes" else "reads"
    text = svg + (f"\nAbove each role, the documents only it {verb}; below the row, the documents "
                  f"more than one role {verb}. Hover a document for its path.\n" if svg else "")
    if everyone:
        text += f"\nEvery role {verb}: " + ", ".join(
            f"{d['name']} (`{d['path']}`)" if d.get("path") else d["name"] for d in everyone) + ".\n"
    return text


def documents_table(roles: list[Role], docs: list[dict]) -> str:
    """The table behind both charts: every document, its path, who writes and who reads it.
    A name that is not a role (a script, a hook, you) is shown as written."""
    by_id = {r.id: r for r in roles}

    def who(value) -> str:
        parts = []
        for rid, note in actors(value):
            r = by_id.get(rid)
            name = "every role" if rid == "all" else linked(r.label, r.rel) if r else rid
            parts.append(f"{name} ({note})" if note else name)
        return cell(", ".join(parts)) or "—"

    stale = any(d.get("stale") for d in docs)
    lines = ["| Document | Written by | Read by |" + (" Stale when |" if stale else ""),
             "|---|---|---|" + ("---|" if stale else "")]
    for d in docs:
        path = ('<br><code class="docutils literal notranslate" style="display:inline-block;min-width:15em;white-space:normal;overflow-wrap:anywhere">'
                + html.escape(cell(d["path"])) + "</code>") if d.get("path") else ""
        lines.append(f"| **{cell(d['name'])}**{path} | {who(d.get('writes'))} | {who(d.get('reads'))} |"
                     + (f" {cell(d.get('stale') or '—')} |" if stale else ""))
    return "\n".join(lines) + "\n"


def drivers_section(drivers: list[dict], skills: dict[str, tuple[Page, bool]], prefix: str) -> str:
    """Each driver as one loop, drawn as a row, and a table of its ledger and what holds it.

    A row reads left to right and back: the ledger tells the driver the next step through a
    script, the driver spawns, the agent returns (dashed), and the step's writer puts the
    result back in the ledger along the bottom. A driver that spawns nothing writes it itself."""
    esc = html.escape
    lw, dw, aw, gap, pad, lh = 200, 150, 200, 124, 10, 13
    lx, dx = pad, pad + lw + gap
    ax = dx + dw + gap
    width = ax + aw + pad
    out: list[str] = []
    table = ["| Driver | The ledger | Held by |", "|---|---|---|"]

    def plain(text) -> str:
        return str(text).replace("`", "")

    def text(lines: list[str], x: float, y: float, cls: str = "df-d") -> None:
        for n, line in enumerate(lines):
            out.append(f'<text class="{cls}" x="{x:.1f}" y="{y + n * lh:.1f}">{esc(line)}</text>')

    y = pad
    for i, d in enumerate(drivers):
        sid, c = str(d["skill"]), PALETTE[i % len(PALETTE)]
        page, typed = skills.get(sid, (None, False))
        name = f"/{prefix}:{sid}" if typed else sid
        ledger = wrap(plain(d.get("ledger", "the ledger")), 34)
        spawns = wrap(plain(d["spawns"]), 34) if d.get("spawns") else []
        nxt = wrap(plain(d.get("next", "")), 21)
        back = wrap(plain(d.get("returns", "")), 21) if spawns else []
        writer = wrap(plain(d.get("writer", "")), 60)
        by_agent = bool(spawns) and d.get("writer_in", "agent") == "agent"
        box = max(40, 14 + lh * max(len(ledger), len(spawns), 2))
        top = y + max(0, lh * len(nxt) + 12 - box // 2)        # room for the label over the arrow
        mid, low = top + box / 2, top + box
        under = max(low, mid + 12 + lh * len(back) + 4) + 20 + lh * (len(writer) - 1 if writer else 0)

        def arrow(path: str, dashed: bool = False) -> None:
            out.append(f'<path class="df-e" d="{path}" stroke="{c}" marker-end="url(#dr-{i})"'
                       + (' stroke-dasharray="4 3"' if dashed else "") + "/>")

        out.append(f'<defs><marker id="dr-{i}" viewBox="0 0 8 8" refX="7" refY="4" markerWidth="7" '
                   f'markerHeight="7" orient="auto"><path d="M0 0L8 4L0 8z" fill="{c}"/></marker></defs>')
        arrow(f"M{lx + lw} {mid - 5}L{dx} {mid - 5}")
        text(nxt, lx + lw + gap / 2, mid - 11 - lh * (len(nxt) - 1))
        if spawns:
            arrow(f"M{dx + dw} {mid - 5}L{ax} {mid - 5}")
            text(["spawns"], dx + dw + gap / 2, mid - 11)
            if back:
                arrow(f"M{ax} {mid + 7}L{dx + dw} {mid + 7}", dashed=True)
                text(back, dx + dw + gap / 2, mid + 7 + lh)
        if writer:
            sx = ax + aw / 2 if by_agent else dx + dw / 2
            arrow(f"M{sx} {low}L{sx} {under}L{lx + lw / 2} {under}L{lx + lw / 2} {low}")
            text(writer, (lx + lw / 2 + dx + dw / 2) / 2, under - 6 - lh * (len(writer) - 1))
        out.append(f'<rect class="df-doc" x="{lx}" y="{top}" width="{lw}" height="{box}" rx="3"/>')
        text(ledger, lx + lw / 2, mid + 4 - lh * (len(ledger) - 1) / 2)
        drv = (f'<rect class="df-role" x="{dx}" y="{top}" width="{dw}" height="{box}" rx="6" stroke="{c}"/>'
               f'<text class="df-t" x="{dx + dw / 2}" y="{mid - 2}">{esc(sid)}</text>'
               f'<text class="df-n" x="{dx + dw / 2}" y="{mid + 12}">driver, main chat</text>')
        out.append(f'<a href="{esc(page.rel[:-3])}.html">{drv}</a>' if page else drv)
        if spawns:
            out.append(f'<rect class="df-role" x="{ax}" y="{top}" width="{aw}" height="{box}" rx="6" '
                       f'stroke="{c}" stroke-dasharray="5 3"/>')
            text(spawns, ax + aw / 2, mid + 4 - lh * (len(spawns) - 1) / 2)
        y = (under if writer else low) + 26
        table.append(f"| {linked(f'`{name}`', page.rel if page else None)} | {cell(d.get('ledger', '—'))} | "
                     f"{cell(d.get('held', '—'))} |")
    height = y - 26 + pad
    svg = (f'<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 {width} {height:.0f}" role="img" '
           f'style="display:block;width:100%;height:auto;max-width:{width}px"><style>{CHART_CSS}</style>'
           + "\n".join(out) + "</svg>")
    return ('```{raw} html\n<div class="driverflow" style="overflow-x:auto;margin:1em 0">\n' + svg
            + "\n</div>\n```\n\nIn each row the ledger is on the left, the driver in the middle and what it "
              "spawns on the right; the dashed arrow is the agent's return, and the arrow along the bottom "
              "is the one writer of the ledger.\n\n" + "\n".join(table) + "\n")


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
    out = site / "docs"
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
    flow_cfg = cfg.get("flow") or {}
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

    # Reference: what a reader looks up rather than follows (states, record formats, gotchas).
    reference: list[Page] = []
    ref_dir = site / "reference"
    if ref_dir.exists():
        files = {p.stem: p for p in ref_dir.glob("*.md")}
        for stem in ordered(files, cfg.get("reference_order") or []):
            p = files[stem]
            text = p.read_text()
            h1 = next((l[2:].strip() for l in text.splitlines() if l.startswith("# ")), stem)
            reference.append(add(Page(f"reference/{p.name}", h1, text, p), p))

    # Agents and commands
    agents, commands = [], []
    preloaded: dict[str, list[str]] = {}    # agent -> the skills its frontmatter preloads
    for p in sorted((bundle / "agents").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        preloaded[p.stem] = [x for x in re.split(r"[,\s\[\]]+", fm.get("skills", "")) if x]
        agents.append(add(Page(f"agents/{p.stem}.md", p.stem,
                               head(f"agent: {p.stem}", f"agents/{p.name}", fm) + demote(body), p), p))
    for p in sorted((bundle / "commands").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        commands.append(add(Page(f"commands/{p.stem}.md", f"/{prefix}:{p.stem}",
                                 head(f"/{prefix}:{p.stem}", f"commands/{p.name}", fm) + demote(body), p), p))

    # Skills: SKILL.md is the page, references/ are its children.
    wf_skills: dict[str, Page] = {}
    knowledge: list[Page] = []
    skill_pages: dict[str, tuple[Page, bool]] = {}   # skill -> (its page, whether a person types it)
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
        skill_pages[skill] = (page, user_run)
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

    # ---- the flow page's generated parts, filled where its markers are.
    if flow_page is None and (agents or flow_cfg):
        flow_page = add(Page("flow.md", "The flow", DEFAULT_FLOW))
    if flow_page is not None:
        roles = flow_roles(flow_cfg, {a.title: a for a in agents}, skill_pages)
        docs = flow_cfg.get("documents") or []
        parts = {
            "agents-skills": uses_table(roles, flow_cfg, preloaded, skill_pages),
            "writes": chart_section(roles, docs, "writes"),
            "reads": chart_section(roles, docs, "reads"),
            "documents": documents_table(roles, docs) if docs else "",
            "drivers": drivers_section(flow_cfg["drivers"], skill_pages, prefix) if flow_cfg.get("drivers") else "",
        }
        marked = set(FLOW_MARK.findall(flow_page.text))
        for part in marked - set(FLOW_PARTS):
            print(f"  ! site/flow.md: <!-- flow:{part} --> is not a part this builder fills")
        for part in FLOW_PARTS:
            if parts[part] and part not in marked and (part != "agents-skills" or agents):
                print(f"  ! site/flow.md has no <!-- flow:{part} --> line, so that part is not on the page")
        flow_page.text = FLOW_MARK.sub(
            lambda m: parts.get(m.group(1)) or (m.group(0) if m.group(1) not in parts else
                                               f"*Nothing under `flow:` in `site/site.yml` for this part yet.*\n"),
            flow_page.text)
        known = {r.id for r in roles} | {"all"}
        others = sorted({a for d in docs for k in ("writes", "reads") for a, _ in actors(d.get(k))} - known)
        if others:
            print(f"  flow: in the documents table only, not a role in the charts: {', '.join(others)}")

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
        + toc("Workflows", workflows) + toc("Reference", reference) \
        + toc("Agents", agents) + toc("Commands", commands) \
        + toc("Workflow skills", wf_pages) + toc("Knowledge skills", knowledge) \
        + toc("Scripts", scripts) + toc("Rules and config", rules_config) \
        + toc("Notes", notes) + toc("Evals", [evals_page] if evals_page else [])
    (out / "index.md").write_text(index)

    css = site / "extra.css"
    (out / "_static").mkdir()
    (out / "_static" / "extra.css").write_text(
        (css if css.exists() else DEFAULTS / "extra.css").read_text())
    (out / "conf.py").write_text(CONF.format(title=title.replace("'", "\\'"), name=name))

    print(f"{name}: wrote {len(pages) + 1} pages under {out}")
    print(f"  {len(agents)} agents, {len(commands)} commands, {len(workflows)} workflows, "
          f"{len(reference)} reference, "
          f"{len(wf_pages)} workflow skills, {len(knowledge)} knowledge skills, "
          f"{len(scripts)} scripts, {len(rules_config)} rules/config, {len(notes)} notes")

    if args.build:
        build = site / "_build"
        missing = [m for m in ("sphinx", "myst_parser", "furo", "sphinxcontrib.mermaid")
                   if importlib.util.find_spec(m) is None]
        if missing:
            sys.exit(f"  ! not installed: {', '.join(missing)} — "
                     f"pip install sphinx myst-parser furo sphinxcontrib-mermaid")
        r = subprocess.run([sys.executable, "-m", "sphinx", "-b", "html", "-q", str(out), str(build)])
        print(f"  html -> {build}/index.html" if r.returncode == 0 else "  ! sphinx-build failed")
        sys.exit(r.returncode)
    print(f"  build -> python3 -m sphinx -b html {out} {site / '_build'}")


CONF = """\
# Generated by plugin-dev's build_site.py — do not edit; rebuilt on every run.
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
