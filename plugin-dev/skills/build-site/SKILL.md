---
name: build-site
description: Build or refresh the Sphinx reading site for a Claude Code plugin — every agent, command, skill (with its references as children), script, rule and config file rendered as a browsable site with a generated nav. Use only in a plugin repo (one containing .claude-plugin/plugin.json), after editing any agent or skill, or when someone wants to read the bundle rather than grep it.
argument-hint: "[bundle path] [--evals evals.json] [--build]"
---

# Build the reading site

One builder serves every plugin. It lives in this kit, not in the plugin repos, so a fix to
the nav or the page layout reaches all of them at once.

## Run it

From the plugin repo root:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_site.py" --build
```

`CLAUDE_PLUGIN_ROOT` is only set when this plugin is installed. When it is not — a sandbox, a
session that has the repo but not the plugin — use the path inside the repo instead, from the
plugin repo root:

```
python3 ../plugin-dev/scripts/build_site.py --build
```

The bundle defaults to the current directory. Pass a path to build a different repo, and
`--evals evals.json` to add an Evals page. Without `--build` the script writes the source tree
only (`site/docs/`); with it, Sphinx renders HTML into `site/_build/` and the entry page is
`site/_build/index.html`.

`sphinx`, `myst-parser`, `furo`, `sphinxcontrib-mermaid` and `pyyaml` must be installed once
per machine: `pip install sphinx myst-parser furo sphinxcontrib-mermaid pyyaml`. The script
names what is missing if `--build` cannot run.

Report what the script printed — the page and section counts are the useful part, because a
count that drops after an edit means a skill or agent stopped being discovered — and any
Sphinx warning, each of which names a page and a line.

## What is generated vs. authored

Generated on every run, and gitignored in every plugin repo — never edit these by hand, they
are overwritten:

- `site/docs/` — the Sphinx source tree: every page, `conf.py`, and `index.md` with the
  toctrees. Rebuilt from scratch.
- `site/_build/` — built HTML, with `--build`

Authored, and committed:

- `site/site.yml` — the only per-plugin config, and every key in it is optional. Reading
  order for workflow pages and workflow skills, the home-page title, the command prefix, and
  any extra config files to render. See `templates/site/site.yml` in this kit.
- `site/flow.md` — the hand-written orientation page: where truth comes from, the loop, the
  hand-offs, the order of authority. Omitted entirely if the plugin has no such page.
- `site/workflows/*.md` — one page per pipeline
- `site/notes/*.md` — design docs and decision records; each gets a nav entry under "Notes"
- `site/notes/<slug>/` — one folder per plan, from `design-plugin` or `review-plugin`,
  `plan-phases` and `run-phase`; only its `<slug>-00-overview.md` gets a nav entry under
  "Notes", so the spec, the phase notes, the findings and the ledger stay in the repo and out
  of the site
- `site/extra.css` — optional per-repo CSS. If absent, the kit's `scripts/defaults/extra.css`
  is used. The theme (Furo) and its teal palette are fixed in the builder, so a theme change
  is an edit to `scripts/build_site.py`, which every plugin shares.

Any change requiring a rebuild that touches what is written in any of the above authored file requires an edit to that file to update it.

## Pages and links

- **A skill is a page and its `references/` are its children.** `skills/<name>/SKILL.md` is
  `skills/<name>/index.html`, and each reference sits beside it and nests under it in the
  sidebar. A link written `references/x.md` in a skill resolves to that child.
- **Scripts are pages.** Every `scripts/*.py`, and `skills/*/scripts/*.py`, is rendered from
  its module docstring, the `--help` of the script and of each subcommand, a table of its
  public functions, and its source. The `--help` is captured by running the script's `main()`
  in a child process in an empty directory until it reaches argparse, so a script that does
  work before parsing arguments can neither write into the repo nor stall the build. Under
  **Scripts** in the nav.
- **A backticked mention of a script links to its page** — any inline code span containing
  `phases.py` or `edits.py`, in a skill, agent, workflow or note. The script's page lists what
  links to it under "Referenced by", so a script's callers are visible from the script.
- **Relative `.md` links are rewritten** to the generated layout, so a link written for GitHub
  works on the site. One that points at a file the site does not render is left as written and
  Sphinx reports it as a warning — fix the link or add the page.

Sources stay written the way GitHub reads them. MyST parses CommonMark, so nothing is
re-indented on the way in, and a numbered list that starts at `0.` or resumes after an aside
counts the way its author wrote it.

## The nav

Fixed shape, and a section with nothing in it is omitted rather than left empty:

    Start (README, the flow) -> Workflows -> Agents -> Commands -> Workflow skills ->
    Knowledge skills -> Scripts -> Rules and config -> Notes -> Evals

Everything is discovered from the bundle, so adding a skill, a `references/` file, a script, a
command or a rule needs no edit anywhere — re-run the script and it appears. The only reason
to touch `site.yml` is to put something earlier in the reading order than alphabetical would.

A skill lands under **Workflow skills** when you are the one who runs it: its frontmatter says
`context: fork` (it forks into an agent) or `disable-model-invocation: true` (only you can start
it, so it is a step even when it runs inline in your conversation). Everything else is a
**Knowledge skill** — material an agent reads.

## If it fails

- *no .claude-plugin/plugin.json* — you are not in a plugin repo root. Pass the root as the
  first argument.
- *not installed: …* — `--build` needs the packages above; the source tree was still written.
- *PyYAML is not installed* — only needed when `site/site.yml` exists. `pip install pyyaml`,
  or delete the file to take the defaults.
- *a Sphinx warning on a page* — it names the generated page under `site/docs/`; the same
  path under the plugin is the source. Never fix the generated file.
