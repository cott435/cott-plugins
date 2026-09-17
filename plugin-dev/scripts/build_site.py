"""Render a Claude Code plugin bundle as an MkDocs site for reading.

Usage:  python3 build_site.py [bundle] [--evals evals.json]

`bundle` is the plugin repo root — the directory holding `.claude-plugin/plugin.json`.
It defaults to the current working directory, so from a plugin repo you can just run the
script with no arguments.

Everything the site shows is discovered from the bundle: every agent, every command, every
skill (plus its `references/`), every rule, the README, and any authored page under
`site/`. Nothing here is specific to one plugin — the only per-plugin knobs live in
`site/site.yml` in the consuming repo, and every one of them is optional.

Writes, all of them generated and safe to gitignore:

    <bundle>/site/docs/        every page, rebuilt from scratch on each run
    <bundle>/site/mkdocs.yml   mkdocs-base.yml plus a generated nav

Authored, and committed, in the consuming repo:

    <bundle>/site/site.yml        optional config (see SITE_YML_DOC below)
    <bundle>/site/flow.md         optional hand-written orientation page
    <bundle>/site/workflows/*.md  one page per pipeline
    <bundle>/site/notes/*.md      design docs and decision records
    <bundle>/site/mkdocs-base.yml optional theme override; the kit default is used if absent
    <bundle>/site/extra.css       optional CSS override; likewise

Nav shape (a section is omitted entirely when it has nothing in it):

    Home (README) -> The flow -> Workflows -> Agents -> Commands ->
    Workflow skills -> Knowledge skills -> Rules and config -> Notes -> Evals
"""

from __future__ import annotations

import argparse
import json
import re
import shutil
import sys
from pathlib import Path

SITE_YML_DOC = """\
# site/site.yml — every key is optional.
site_title: my_plugin            # H1 of the home page (default: the plugin's name)
command_prefix: my-plugin        # workflow skills render as /<prefix>:<skill> (default: plugin name)
workflows_order:                 # reading order for site/workflows/*.md; unlisted files follow
  - new-repo                     # alphabetically, so a new page needs no edit here
workflow_skills_order:           # reading order for the skills you run (`context: fork`, or
                                 # `disable-model-invocation: true`)
  - plan-repo
config_files:                    # extra files rendered verbatim as code under "Rules and config"
  - pyproject-lint-config.toml
"""

KIT = Path(__file__).resolve().parent
DEFAULTS = KIT / "defaults"

FM_RE = re.compile(r"^---\n(.*?)\n---\n", re.S)


# --------------------------------------------------------------------------- parsing

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
                 f"(mkdocs pulls it in), or delete the file to use defaults.")
    return yaml.safe_load(path.read_text()) or {}


def plugin_name(bundle: Path) -> str:
    manifest = bundle / ".claude-plugin" / "plugin.json"
    if not manifest.exists():
        sys.exit(f"no .claude-plugin/plugin.json under {bundle} — is that a plugin repo? "
                 f"(pass the repo root as the first argument)")
    return json.loads(manifest.read_text())["name"]


# --------------------------------------------------------------------------- rendering

def fm_table(fm: dict[str, str]) -> str:
    """Render frontmatter as a two-column table so it is visible in the site."""
    if not fm:
        return ""
    pipe = "\\|"
    rows = "\n".join(f"| `{k}` | {v.replace('|', pipe) or '—'} |" for k, v in fm.items())
    return f"| frontmatter | value |\n|---|---|\n{rows}\n\n"


def demote(body: str) -> str:
    """Shift markdown headings down one level so the page title stays the H1."""
    return re.sub(r"^(#{1,5}) ", lambda m: "#" * (len(m.group(1)) + 1) + " ", body, flags=re.M)


def write_page(docs: Path, rel: str, title: str, fm: dict[str, str],
               body: str, source: str) -> None:
    out = docs / rel
    out.parent.mkdir(parents=True, exist_ok=True)
    head = f"# {title}\n\n*Source: `{source}`*\n\n{fm_table(fm)}"
    out.write_text(head + demote(body))


def ordered(names, preferred: list[str]):
    """`preferred` first in the order given, then everything else alphabetically."""
    listed = [n for n in preferred if n in names]
    return listed + sorted(n for n in names if n not in preferred)


# --------------------------------------------------------------------------- nav

def build_nav(sections: list[tuple[str, list[tuple[str, str]]]],
              flow: bool, evals: bool) -> str:
    lines = ["nav:", "  - Home (README): index.md"]
    if flow:
        lines.append("  - The flow: flow.md")
    for heading, entries in sections:
        if not entries:
            continue
        lines.append(f"  - {heading}:")
        lines += [f"      - {title}: {path}" for title, path in entries]
    if evals:
        lines.append("  - Evals: evals.md")
    return "\n".join(lines) + "\n"


# --------------------------------------------------------------------------- build

def main() -> None:
    ap = argparse.ArgumentParser(description=__doc__.splitlines()[0])
    ap.add_argument("bundle", nargs="?", default=".",
                    help="plugin repo root (default: the current directory)")
    ap.add_argument("--evals", default=None,
                    help="optional evals.json to render as an extra page")
    args = ap.parse_args()

    bundle = Path(args.bundle).resolve()
    name = plugin_name(bundle)
    site = bundle / "site"
    docs = site / "docs"
    cfg = load_config(site)

    title = cfg.get("site_title", name)
    prefix = cfg.get("command_prefix", name)

    site.mkdir(exist_ok=True)
    if docs.exists():
        try:
            shutil.rmtree(docs)
        except OSError as exc:
            # Some sandboxes mount the working folder without delete permission. Pages are
            # rewritten in place below; only a page whose source was renamed or removed can
            # linger, so say so rather than failing the whole build.
            print(f"  ! could not clear {docs} ({exc.strerror}) — rebuilding in place; "
                  f"pages for deleted sources may be stale")
    docs.mkdir(exist_ok=True)

    # Home: the plugin README, headings demoted under a title.
    readme_path = bundle / "README.md"
    if readme_path.exists():
        readme = re.sub(r"^# .*\n", "", readme_path.read_text(), count=1)
        # The README links to site/workflows/*.md for GitHub readers; on the site those
        # pages sit beside index.md under workflows/.
        readme = readme.replace("](site/workflows/", "](workflows/")
        (docs / "index.md").write_text(
            f"# {title}\n\n*Source: `README.md`*\n\n" + demote(readme))
    else:
        (docs / "index.md").write_text(f"# {title}\n\nNo README.md found in the bundle.\n")

    flow = site / "flow.md"
    if flow.exists():
        shutil.copy(flow, docs / "flow.md")

    css = site / "extra.css"
    shutil.copy(css if css.exists() else DEFAULTS / "extra.css", docs / "extra.css")

    # Workflows: one authored page per pipeline in site/workflows/, title from its H1.
    workflows: list[tuple[str, str]] = []
    wf_dir = site / "workflows"
    if wf_dir.exists():
        (docs / "workflows").mkdir(exist_ok=True)
        files = {p.stem: p for p in wf_dir.glob("*.md")}
        for stem in ordered(files, cfg.get("workflows_order") or []):
            p = files[stem]
            shutil.copy(p, docs / "workflows" / p.name)
            h1 = next((l for l in p.read_text().splitlines() if l.startswith("# ")), f"# {stem}")
            workflows.append((h1[2:].strip(), f"workflows/{p.name}"))

    # Agents
    agents: list[tuple[str, str]] = []
    for p in sorted((bundle / "agents").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        write_page(docs, f"agents/{p.stem}.md", f"agent: {p.stem}", fm, body, f"agents/{p.name}")
        agents.append((p.stem, f"agents/{p.stem}.md"))

    # Commands
    commands: list[tuple[str, str]] = []
    for p in sorted((bundle / "commands").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        write_page(docs, f"commands/{p.stem}.md", f"/{prefix}:{p.stem}", fm, body,
                   f"commands/{p.name}")
        commands.append((f"/{prefix}:{p.stem}", f"commands/{p.stem}.md"))

    # Skills — a skill you run is a workflow skill; the rest are knowledge an agent reads.
    # "You run it" means it forks into an agent (`context: fork`) or only a person can start it
    # (`disable-model-invocation: true`) — a skill that runs inline in the conversation, like a
    # status readout or an interview, is still a step in the workflow.
    workflow: dict[str, list[tuple[str, str]]] = {}
    knowledge: list[tuple[str, str]] = []
    for p in sorted((bundle / "skills").glob("*/SKILL.md")):
        fm, body = split_frontmatter(p.read_text())
        skill = p.parent.name
        user_run = (fm.get("context") == "fork"
                    or str(fm.get("disable-model-invocation", "")).strip().lower() == "true")
        kind = "workflow" if user_run else "knowledge"
        stitle = f"/{prefix}:{skill}" if kind == "workflow" else skill
        rel = f"skills/{kind}/{skill}.md"
        write_page(docs, rel, stitle, fm, body, f"skills/{skill}/SKILL.md")
        if kind == "workflow":
            workflow.setdefault(skill, []).append((stitle, rel))
        else:
            knowledge.append((stitle, rel))
        # A skill's reference files are listed with the skill that owns them. Filing a workflow
        # skill's references under Knowledge skills separates a page from the only thing that
        # explains it, and implies an agent reads it on its own.
        refs = p.parent / "references"
        if refs.exists():
            for r in sorted(refs.glob("*.md")):
                rrel = f"skills/{kind}/{skill}-{r.stem}.md"
                write_page(docs, rrel, f"{skill} / {r.stem}", {}, r.read_text(),
                           f"skills/{skill}/references/{r.name}")
                entry = (f"{skill} / {r.stem}", rrel)
                (workflow[skill] if kind == "workflow" else knowledge).append(entry)

    wf_skills = [e for n in ordered(workflow, cfg.get("workflow_skills_order") or [])
                 for e in workflow[n]]

    # Rules and config
    rules_config: list[tuple[str, str]] = []
    for p in sorted((bundle / "rules").glob("*.md")):
        fm, body = split_frontmatter(p.read_text())
        write_page(docs, f"rules/{p.name}", f"rule: {p.stem}", fm, body, f"rules/{p.name}")
        rules_config.append((f"rule {p.stem}", f"rules/{p.name}"))
    for rel in cfg.get("config_files") or []:
        p = bundle / rel
        if not p.exists():
            print(f"  ! config_files lists {rel}, which does not exist — skipped")
            continue
        (docs / "config").mkdir(exist_ok=True)
        lang = p.suffix.lstrip(".") or "text"
        (docs / "config" / f"{p.stem}.md").write_text(
            f"# {p.name}\n\n*Source: `{rel}`*\n\n```{lang}\n{p.read_text()}\n```\n")
        rules_config.append((p.name, f"config/{p.stem}.md"))

    # Notes: anything dropped in site/notes/
    notes: list[tuple[str, str]] = []
    notes_dir = site / "notes"
    if notes_dir.exists():
        for n in sorted(notes_dir.glob("*.md")):
            shutil.copy(n, docs / f"note-{n.name}")
            notes.append((n.stem.replace("-", " "), f"note-{n.name}"))

    # Evals, if given
    has_evals = False
    if args.evals:
        data = json.loads(Path(args.evals).read_text())
        lines = ["# Eval definitions\n", f"*Source: `{Path(args.evals).name}`*\n",
                 f"\n{data.get('notes', '')}\n"]
        for e in data["evals"]:
            lines.append(
                f"\n## {e['id']} — {e['name']}\n\n**Invocation:** `{e['invocation']}`  \n"
                f"**Fixture:** {e['fixture']}\n\n**Prompt:** {e['prompt']}\n\n"
                f"**Expected:** {e['expected_output']}\n")
        (docs / "evals.md").write_text("\n".join(lines))
        has_evals = True

    nav = build_nav([
        ("Workflows", workflows),
        ("Agents", agents),
        ("Commands", commands),
        ("Workflow skills", wf_skills),
        ("Knowledge skills", knowledge),
        ("Rules and config", rules_config),
        ("Notes", notes),
    ], flow=flow.exists(), evals=has_evals)

    base_path = site / "mkdocs-base.yml"
    if base_path.exists():
        base = base_path.read_text()
    else:
        base = (DEFAULTS / "mkdocs-base.yml").read_text() \
            .replace("__SITE_NAME__", title).replace("__PLUGIN_NAME__", name)
    (site / "mkdocs.yml").write_text(base + "\n" + nav)

    print(f"{name}: wrote {sum(1 for _ in docs.rglob('*.md'))} pages under {docs}")
    print(f"  {len(agents)} agents, {len(commands)} commands, {len(workflows)} workflows, "
          f"{len(wf_skills)} workflow skills, {len(knowledge)} knowledge pages, "
          f"{len(rules_config)} rules/config, {len(notes)} notes")
    print(f"  nav -> {site / 'mkdocs.yml'}   (cd {site} && mkdocs serve)")


if __name__ == "__main__":
    main()
