# Versioning — `plugin-dev`

The policy (what triggers a patch/minor/major bump, the bump + CHANGELOG + tag + marketplace
procedure, and the `model:` field policy) lives in the `plugin-dev` plugin's `bump-version`
skill, shared by every plugin. This file records only what is specific to this one.

## Model decisions

Two agents. `run-auditor` (spawned by `audit-run`) is on `inherit`. An audit is judgment over
a long trace. A cheaper model misses the claims-versus-evidence mismatches that are the point
of the check, and the person running an audit has already chosen the session model for it.

`run-narrator` (spawned by `run-flow --explain`) is on `claude-sonnet-5-5`, a full id because
an alias moves (`plugin-anatomy`, `references/agents.md`, **Model names**). It writes a reading
aid whose every line links to the steps it cites, so a cheaper model is enough and the cost of
a 12-unit run stays under a million tokens.

`run-evals`' agents — executors, graders and comparators, all general-purpose subagents with
no agent file — run on Sonnet 5.5 (the user's decision, 2026-09-29, first applied in dev-team
2.2 phase 8). `skills/run-evals/SKILL.md` **The model** says how that is asked for in the
Agent tool and in a headless run, which differ.

## Exceptions

**Breaking changes here are breaking changes everywhere.** `scripts/build_site.py` is
consumed by every plugin repo, so a change to what it reads — the shape of `site.yml`, the
files it discovers, where it writes — is MAJOR even though nothing in this repo's own
manifest changed. The same is true of a skill rename: other repos' `CLAUDE.md` files name
these skills.
