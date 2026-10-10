# <name>

<One paragraph: what this plugin does, and for whom.>

## How it runs

<The workflow in a few lines, by the parts every workflow here has: the driver you type and
what it holds, the agents it spawns and what each returns, the scripts and hooks that decide
what is next and what must hold, and the ledger a run picks up from. Then why it is built
that way for this job. No list of skills or agents and no step-by-step: the site has both.>

## Install

```
/plugin marketplace add cott435/cott-plugins
/plugin install <name>@cott-plugins
```

## The reading site

Every agent, skill and script as a browsable site, with a flow page that maps which role
uses which skill, who writes and reads each document, and how each driver runs:

```
python3 ~/dev/cott-plugins/plugin-dev/scripts/build_site.py --build   # from this directory
python3 -m http.server --directory site/_build 8000                   # http://127.0.0.1:8000
```

Needs `pip install sphinx myst-parser furo sphinxcontrib-mermaid pyyaml` once per machine.
Or ask Claude: the `build-site` skill from `plugin-dev` does the same thing. `site/docs/`
and `site/_build/` are generated and gitignored; `site/site.yml`, `site/flow.md`,
`site/workflows/` and `site/notes/` are authored and committed.

## Working on it

Read `CLAUDE.md` first. Versioning, eval logging, the contracts check and the site builder
are shared across all plugins and live in the `plugin-dev` plugin, not here.
