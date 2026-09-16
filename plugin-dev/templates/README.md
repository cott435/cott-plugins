# <name>

<One paragraph: what this plugin does, and for whom.>

## Install

```
/plugin marketplace add cott435/cott-plugins
/plugin install <name>@cott-plugins
```

## What's here

| Path | What it is |
|---|---|
| `agents/` | The specialist subagents. |
| `skills/` | The skills — one directory each, with `SKILL.md`. |
| `evals/` | Test runs against this plugin's own agents and skills. See `evals/README.md`. |
| `site/` | The authored parts of the reading site (see below). |
| `VERSIONING.md` | This plugin's versioning decisions. Policy is in `plugin-dev`. |
| `CLAUDE.md` | Instructions for working on this repo's source. |

## The reading site

Every agent, command, skill and rule rendered as a browsable MkDocs site:

```
python3 ~/dev/cott-plugins/plugin-dev/scripts/build_site.py     # from this repo root
cd site && mkdocs serve                            # http://127.0.0.1:8000
```

Or ask Claude — the `build-site` skill from `plugin-dev` does the same thing. `site/docs/`
and `site/mkdocs.yml` are generated and gitignored; `site/site.yml`, `site/flow.md`,
`site/workflows/` and `site/notes/` are authored and committed.

## Working on it

Read `CLAUDE.md` first. Versioning, eval logging and the site builder are shared across all
plugins and live in the `plugin-dev` plugin, not in this repo.
