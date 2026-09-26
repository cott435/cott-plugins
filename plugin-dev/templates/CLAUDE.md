# CLAUDE.md

Instructions for working on this subdirectory — the `<name>` plugin's own source (its
agents, skills, and site) — not a repo the plugin is used to plan or build. The general
protocol (versioning, eval logging, contract checks, the site builder) is the repo root
`CLAUDE.md`; this file holds only what's specific to this plugin.

## The shared protocol is in the parent, and it is not optional

The repo root `CLAUDE.md` carries the rules this plugin is maintained by — when `build-site`,
`log-eval`, `check-contracts` and `bump-version` run, and which of them ask first. A session
that mounts only this folder cannot read it, and will edit skills without ever rebuilding the
site or proposing a version bump. So: if `../CLAUDE.md` cannot be read, say so and ask for
`cott-plugins` to be connected before making changes here.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions — currently its per-agent
`model:` choices. The policy itself is `plugin-dev`'s `bump-version`.

<!-- Add anything specific to this plugin's source below. -->
