# CLAUDE.md

Instructions for working on this subdirectory — the `dev-team` plugin's own source
(its agents, skills, and site) — not a repo the plugin is used to plan or build. The general
protocol (versioning, eval logging, the site builder) is the repo root `CLAUDE.md`; this file
holds only what's specific to this plugin.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions: the per-agent `model:` choices —
every agent on `inherit`, with the overrides considered and why none is applied — and nothing
else. The policy itself is `plugin-dev`'s `bump-version`.

## Adding a skill means updating two files

A new skill here — workflow or knowledge — is added, in the same change, to:

1. `README.md`'s **Contents** tree, and its knowledge-scope table if it is a knowledge skill;
2. `site/site.yml`'s `workflow_skills_order`, if it is a workflow skill.

A skill *removed* comes out of both. `plugin-dev`'s `check-contracts` fails on both, in both
directions — a skill missing from a list, and a name in a list with no such skill — so run it
after any change under `skills/`. It is the rule's enforcement, not a reminder of it: the two
claims are `contracts.yml`'s two `names_listed` entries. Item 2 covers the workflow skills
only, selected by `disable-model-invocation: true` rather than by a second list. The plugin's
own skill names are never listed anywhere else: at run time the architect derives them with
`ls ${CLAUDE_PLUGIN_ROOT}/skills`.

## The flow page is drawn from `site/site.yml`

`site/flow.md`'s table of agents and skills, its two document charts, the documents table
and the driver's row are drawn by `plugin-dev`'s `build-site` from the `flow:` block of
`site/site.yml` and each agent's `skills:` frontmatter. An agent that starts invoking a
skill, a document under `docs/` that gains a writer or a reader or changes when it goes
stale, or a change to the driver's hooks is an edit to that block, in the same change. It
replaced the hand-written `docs/` map, so there is no second copy to keep in step.

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
