# The reading site

Renders the plugin — every agent, every skill, the rule, the lint config — as a browsable
MkDocs site. The bundle itself stays the source of truth; this only mirrors it.

The builder is **not in this repo**. It lives in the `plugin-dev` plugin, shared by every
plugin, so a fix to the nav or the page layout reaches all of them at once. See
`plugin-dev/skills/build-site/SKILL.md` for the full contract.

## Build and read

```bash
pip install mkdocs mkdocs-material pymdown-extensions   # once per machine
python3 ~/dev/cott-plugins/plugin-dev/scripts/build_site.py          # from the repo root
cd site && mkdocs serve                                 # then open http://127.0.0.1:8000
```

Or ask Claude — the `build-site` skill does the same thing. The bundle defaults to the
current directory, so the script needs no arguments. Re-run it after editing any agent or
skill; the nav is generated from what it finds, so a new skill or a new `references/` file
appears without editing any config.

Optional: `--evals evals.json` adds an Evals page.

## What is generated vs. authored

Generated, and gitignored — never edit these by hand:

- `docs/` — every page, rebuilt from scratch on each run
- `mkdocs.yml` — the base config plus a generated nav
- `_site/` — the built HTML, if you run `mkdocs build`

Authored, and committed:

- `site.yml` — the only config: reading order for the workflow pages and the workflow
  skills, and the lint config file to render. Every key is optional.
- `workflows/*.md` — one page per pipeline (new repo, adding a package, changing shipped
  code, adopting an existing repo, …); reading order is `workflows_order` in `site.yml`,
  unlisted files follow alphabetically
- `flow.md` — the hand-written orientation page: where truth comes from, the loop,
  the hand-offs, the order of authority
- `notes/*.md` — drop any design doc or decision record here and it gets a nav entry
  under "Notes"

This repo does **not** carry `mkdocs-base.yml` or `extra.css`: the kit's defaults produce an
identical site. Add either file here only to override the theme for this plugin alone.
