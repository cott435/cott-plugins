# CLAUDE.md

Instructions for working on this subdirectory — the `dev-team` plugin's own source
(its agents, skills, and site) — not a repo the plugin is used to plan or build. The general
protocol (versioning, eval logging, the site builder) is the repo root `CLAUDE.md`; this file
holds only what's specific to this plugin.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions — the per-agent `model:` choices
and the untagged `1.1.0` loose end.

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
