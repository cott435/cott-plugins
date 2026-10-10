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
`site/_build/index.html`. To read it, serve the folder:

```
python3 -m http.server --directory site/_build 8000      # http://127.0.0.1:8000
```

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
  order for workflow pages and workflow skills, the home-page title, the command prefix, any
  extra config files to render, and the `flow:` block the flow page is drawn from. See
  `templates/site/site.yml` in this kit.
- `site/flow.md` — the map of the plugin, with the same parts in every plugin. See **The
  flow page**, below. A plugin with agents and no such file gets a page of the generated
  parts alone.
- `README.md` — the home page. See **The README**, below.
- `site/workflows/*.md` — one page per pipeline
- `site/notes/*.md` — design docs and decision records; each gets a nav entry under "Notes"
- `site/notes/<slug>/` — one folder per plan, from `design-plugin` or `revise-plugin`,
  `plan-phases` and `run-phase`; only its `<slug>-00-overview.md` gets a nav entry under
  "Notes", so the spec, the phase notes, the findings and the ledger stay in the repo and out
  of the site
- `site/extra.css` — optional per-repo CSS. If absent, the kit's `scripts/defaults/extra.css`
  is used. The theme (Furo) and its teal palette are fixed in the builder, so a theme change
  is an edit to `scripts/build_site.py`, which every plugin shares.

Any change requiring a rebuild that touches what is written in any of the above authored file requires an edit to that file to update it.

## The flow page

`site/flow.md` holds the prose and one marker line where each generated part goes. The
builder fills a marker from the bundle and from `flow:` in `site/site.yml`, so the table and
the charts are one set of facts drawn four ways and cannot disagree with each other.

| In `site/flow.md` | Drawn from | Shows |
|---|---|---|
| **Which route**, written by hand | — | which command to type for which kind of work, and the workflow page for each |
| `<!-- flow:agents-skills -->` | every agent's `skills:` frontmatter, plus `flow.uses` | a table of roles against skills: ● always, ○ only on a condition, and the conditions |
| `<!-- flow:writes -->` | `flow.documents[].writes` | the roles in one row; above each, the documents only it writes; below the row, the documents several write, an arrow from each writer |
| `<!-- flow:reads -->` | `flow.documents[].reads` | the same chart for reading, the arrows pointing from the document to the role |
| `<!-- flow:documents -->` | `flow.documents` | the table behind both charts: path, written by, read by, and `stale` when given |
| `<!-- flow:drivers -->` | `flow.drivers` | one row per driver: the ledger, the script that prints the next step, what it spawns, what comes back, the ledger's one writer; then a table of the hooks that hold it |

The `flow:` block:

```yaml
flow:
  roles:            # left to right in the charts. Default: every agent, alphabetically.
    - {id: run-package, note: driver, relays: true} # an agent or a skill, by name
    - {id: unit-agent, label: unit agent, file: skills/x/references/unit-prompt.md}
                                                    # anything else: a label, and the file that defines it
  uses:             # beyond what an agent's frontmatter preloads
    implementer:
      always: [project-structure]
      sometimes:
        - security-review: a trigger in its description matches
      names: [workspace-scaffold]                   # its file mentions it and does not run it
  documents:
    - name: the design                              # the label in the charts: keep it short
      path: docs/packages/<pkg>/design/<section>.md
      match: "design/"                              # optional: how role files name it, if not by path
      writes: [designer]                            # a role, or {role: a note for the table}
      reads: [tester, implementer, {reviewer: round 1}]
      names: [architect]                            # its file mentions the document and does not touch it
      stale: its contract row changed               # optional column
  drivers:
    - skill: run-package
      ledger: derived from disk by `status.py`
      next: "`status.py`"
      spawns: every ready section's next agent, in one message
      returns: "Result: done | blocked | spec-change"
      writer: each agent's own files, and the stop gate's record
      held: "`gate_on_stop.py` on `SubagentStop`"
```

A name in `writes` or `reads` that is not a role (a script, a hook, you) appears in the
documents table as written and in neither chart; the build prints those names, which is
where a misspelled role shows up. `all` means every role and moves the document from the
chart to its caption. A document one role writes is drawn above that role, and one several
write is drawn below the row, so the charts need no layout config.

The block is written by hand and held to the files by `check-contracts`: a `flow` claim in
the plugin's `contracts.yml` fails when a role's file names a skill or a document the block
does not place for that role, when the block lists one the file never names, when an agent
is no role, and when a hook is wired and no driver names it. So a role that starts running
a skill, a document that gains a writer or a reader, or a new hook stops the next
`check-contracts` until the block says so; `names`, `match`, `file` and `relays` exist for
that check and draw nothing. Every plugin with a `flow:` block declares the claim. The build
itself warns when the block has a part and `flow.md` has no marker for it.

## The README

The README is the site's home page and the plugin's page on GitHub, and it holds what the
generated pages cannot: what the plugin is for, how its workflows are driven and why they
are built that way, how to install it, how to build this site, and any overview a reader
needs before the rest. It carries no table of skills or agents and no workflow
walk-throughs: the site lists the first from the bundle, and `site/workflows/` holds the
second. `templates/README.md` is the starting shape.

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
