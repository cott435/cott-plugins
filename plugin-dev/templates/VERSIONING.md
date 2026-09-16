# Versioning — `<name>`

The policy (what triggers a patch/minor/major bump, the bump + CHANGELOG + tag + marketplace
procedure, and the `model:` field policy) lives in the `plugin-dev` plugin's `bump-version`
skill, shared by every plugin. This file records only what is specific to this one.

## Model decisions

Every agent currently sets `model: inherit`. Overrides applied, and why:

| Agent | Model | Why |
|---|---|---|
| — | — | none yet |

Pin a **dated** model ID rather than a rolling alias for any agent under active eval, so a
silent model upgrade later doesn't get mistaken for a prompt regression.

## Exceptions

<!-- Anything where this plugin deliberately departs from the shared policy, and why. -->

None.
