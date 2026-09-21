---
name: build-site
description: Build or refresh the MkDocs reading site for a Claude Code plugin — every agent, command, skill, rule and config file rendered as a browsable site with a generated nav. Use only in a plugin repo (one containing .claude-plugin/plugin.json), after editing any agent or skill, or when someone wants to read the bundle rather than grep it.
argument-hint: "[bundle path] [--evals evals.json]"
---

# Build the reading site

One builder serves every plugin. It lives in this kit, not in the plugin repos, so a fix to
the nav or the page layout reaches all of them at once.

## Run it

From the plugin repo root:

```
python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_site.py"
```

`CLAUDE_PLUGIN_ROOT` is only set when this plugin is installed. When it is not — a sandbox, a
session that has the repo but not the plugin — use the path inside the repo instead, from the
plugin repo root:

```
python3 ../plugin-dev/scripts/build_site.py
```

The bundle defaults to the current directory. Pass a path to build a different repo, and
`--evals evals.json` to add an Evals page. Then:

```
cd site && mkdocs serve      # http://127.0.0.1:8000
```

`mkdocs`, `mkdocs-material` and `pymdown-extensions` must be installed once per machine:
`pip install mkdocs mkdocs-material pymdown-extensions mdx_truly_sane_lists`.

Report what the script printed — the page and section counts are the useful part, because a
count that drops after an edit means a skill or agent stopped being discovered.

## What is generated vs. authored

Generated on every run, and gitignored in every plugin repo — never edit these by hand, they
are overwritten:

- `site/docs/` — every page, rebuilt from scratch
- `site/mkdocs.yml` — the base config plus a generated nav
- `site/_site/` — built HTML, if someone runs `mkdocs build`

Authored, and committed:

- `site/site.yml` — the only per-plugin config, and every key in it is optional. Reading
  order for workflow pages and workflow skills, the home-page title, the command prefix, and
  any extra config files to render. See `templates/site/site.yml` in this kit.
- `site/flow.md` — the hand-written orientation page: where truth comes from, the loop, the
  hand-offs, the order of authority. Omitted entirely if the plugin has no such page.
- `site/workflows/*.md` — one page per pipeline
- `site/notes/*.md` — design docs and decision records; each gets a nav entry under "Notes"
- `site/mkdocs-base.yml`, `site/extra.css` — optional per-repo overrides. If absent, the
  kit's defaults in `scripts/defaults/` are used with the plugin's name substituted in, so a
  new plugin gets a working site with no config at all.

## The nav

Fixed shape, and a section with nothing in it is omitted rather than left empty:

    Home (README) -> The flow -> Workflows -> Agents -> Commands ->
    Workflow skills -> Knowledge skills -> Rules and config -> Notes -> Evals

Everything is discovered from the bundle, so adding a skill, a `references/` file, a command
or a rule needs no edit anywhere — re-run the script and it appears. The only reason to touch
`site.yml` is to put something earlier in the reading order than alphabetical would.

A skill lands under **Workflow skills** when you are the one who runs it: its frontmatter says
`context: fork` (it forks into an agent) or `disable-model-invocation: true` (only you can start
it, so it is a step even when it runs inline in your conversation). Everything else is a
**Knowledge skill** — material an agent reads. A skill's `references/*.md` are always listed as knowledge pages.

## If it fails

- *no .claude-plugin/plugin.json* — you are not in a plugin repo root. Pass the root as the
  first argument.
- *could not clear site/docs* — a sandbox mounted the folder without delete permission. The
  build still ran and rewrote every page in place; only a page whose source was renamed or
  deleted can linger. Remove `site/docs/` yourself and re-run if that matters.
- *PyYAML is not installed* — only needed when `site/site.yml` exists. `pip install pyyaml`,
  or delete the file to take the defaults.
