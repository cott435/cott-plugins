# Versioning — `plugin-dev`

The policy (what triggers a patch/minor/major bump, the bump + CHANGELOG + tag + marketplace
procedure, and the `model:` field policy) lives in the `plugin-dev` plugin's `bump-version`
skill, shared by every plugin. This file records only what is specific to this one.

## Model decisions

This plugin has no agents — it is skills and scripts only — so there is no `model:` field to
set anywhere in it.

## Exceptions

**Breaking changes here are breaking changes everywhere.** `scripts/build_site.py` is
consumed by every plugin repo, so a change to what it reads — the shape of `site.yml`, the
files it discovers, where it writes — is MAJOR even though nothing in this repo's own
manifest changed. The same is true of a skill rename: other repos' `CLAUDE.md` files name
these skills.
