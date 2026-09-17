# CLAUDE.md

Instructions for working on this subdirectory — `plugin-dev`'s own source (its skills,
scripts, templates) — not the general protocol, which is the repo root `CLAUDE.md` and
applies here the same as everywhere else in `cott-plugins`.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions. It has no agents, so there's
no `model:` field to set — see that file for why.

## This plugin in particular

It defines the protocol every other plugin in this repo follows, so two things need extra
care when editing it:

- **Skill descriptions.** These skills are installed on every machine and are live in every
  session, including sessions that have nothing to do with plugins. Each description says
  "only inside a plugin's own subdirectory (one containing `.claude-plugin/plugin.json`)"
  for that reason. If you widen a description, check it doesn't start firing in unrelated
  repos.
- **`scripts/build_site.py` is shared.** A change to it changes every plugin's site at once.
  Before committing one, rebuild at least `dev-team` and diff the output — its site is
  the reference the builder was verified against.
