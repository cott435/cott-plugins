# CLAUDE.md

Instructions for working on this subdirectory — the `dev-team` plugin's own source
(its agents, skills, and site) — not a repo the plugin is used to plan or build. The general
protocol (versioning, eval logging, the site builder) is the repo root `CLAUDE.md`; this file
holds only what's specific to this plugin.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions: the per-agent `model:` choices —
every agent on `inherit`, with the overrides considered and why none is applied — and nothing
else. The policy itself is `plugin-dev`'s `bump-version`.

## Adding a skill

A new workflow skill (one with `disable-model-invocation: true`) is added, in the same
change, to `site/site.yml`'s `workflow_skills_order`; a skill removed comes out of it.
`plugin-dev`'s `check-contracts` fails in both directions, so run it after any change under
`skills/`. A knowledge skill is listed nowhere by hand: the site finds it, and the flow
page's table shows which agents use it once an agent's file names it (below). At run time
the architect derives the plugin's own skill names with `ls ${CLAUDE_PLUGIN_ROOT}/skills`.

## The README holds no reference

`README.md` says what the plugin is for, how it runs and why, where you are asked, and how
to install it and build the site. What a reader looks up is under `site/reference/`: running
a package and the states, the records, the hooks, code conventions, the `docs/` layout,
gotchas and upgrade notes. A change to any of those is an edit to its reference page, and an
upgrade note is a bullet in `site/reference/gotchas.md`. `contracts.yml` sweeps those pages
wherever it sweeps the README.

## The flow page is drawn from `site/site.yml`

`site/flow.md`'s table of agents and skills, its two document charts, the documents table
and the driver's row are drawn by `plugin-dev`'s `build-site` from the `flow:` block of
`site/site.yml` and each agent's `skills:` frontmatter. An agent that starts invoking a
skill, a document under `docs/` that gains a writer or a reader or changes when it goes
stale, or a change to the driver's hooks is an edit to that block, in the same change, and
`check-contracts`' `flow` claim fails until it is made: an agent file that names a skill or
a document the block does not place for that agent, or the reverse. It replaced the
hand-written `docs/` map, so there is no second copy to keep in step.

## The shared protocol is in the parent, and it is not optional

The repo root `CLAUDE.md` carries the rules this plugin is maintained by — when `build-site`,
`log-eval` and `bump-version` run, and which of them ask first. A session that mounts only this
folder cannot read it, and will edit skills without ever rebuilding the site or proposing a
version bump. So: if `../CLAUDE.md` cannot be read, say so and ask for `cott-plugins` to be
connected before making changes here.

After editing any agent or skill, rebuild the site — `build-site` if the plugin is installed,
otherwise the script directly, from this directory:

```
python3 ../plugin-dev/scripts/build_site.py
```
