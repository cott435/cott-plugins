---
name: extract-legacy
description: Mine an old codebase for resources worth carrying into a rebuild - API clients, schemas, parsers, validators, algorithms - and turn each one the user keeps into a project skill under .claude/skills/ that the architect assigns and designers and implementers invoke. The first run drafts docs/legacy/inventory.md and stops; mark keep on each row and re-run to extract. Run before /dev-team:plan-repo so the architect sees the skills.
argument-hint: "<path to the old repo - required on the first run, ignored afterwards>"
context: fork
agent: dev-team:curator
background: false
disable-model-invocation: true
---

Curate the legacy repo at:

$ARGUMENTS

> **Guard.** If you can see earlier conversation turns, or you have an `AskUserQuestion` tool, you are
> running in the main conversation rather than as the `curator` subagent — the agent is not
> registered, usually because the dev-team plugin was installed or updated after Claude
> Code started. Stop, tell the user to run `/reload-plugins` (or restart Claude Code),
> verify with `/agents`, and re-run. Do not survey in the main thread.

## Run gate

`python3 ${CLAUDE_PLUGIN_ROOT}/skills/status/scripts/status.py --run-gate`. FAIL → return
`Result: blocked` with its lines, and write nothing.

## Two modes, decided by what exists

- **Survey** — no `docs/legacy/inventory.md`. The argument is required: the path to the old
  repo, absolute or relative to this repo's root. It must be outside this repo's `packages/`
  directory — a sibling directory or a path elsewhere on disk are both fine. With no argument,
  return a blocker asking for the path. Draft the inventory per your instructions and stop.
- **Extract** — `docs/legacy/inventory.md` exists. Ignore the argument; the old repo path and
  commit are in the inventory's heading. Act on every row with `keep: yes` and
  `status: pending`.

## Before extracting

- Create `.claude/skills/` if it does not exist; create nothing else outside it.
- A row whose `skill` directory already exists is `failed: skill exists`, unless the user
  reset its `status` to `pending` — then the researcher overwrites it.

## Steps

Survey: your **Survey** steps 1–5, ending with the stop message.

Extract: your **Extract** steps 1–4 — spawn every researcher in one message, wait for all of
them, update the inventory, commit per your **Commit** section — trailer
`Dev-Team-Run: extract-legacy $ARGUMENTS` — and return. A Survey run commits the inventory the
same way before its stop message.

## Constraints

- `docs/legacy/inventory.md` is the only file you write; skills are written by researchers.
- A row's `skill` name is never refused for matching one of this plugin's own skills: a plugin
  skill never lives under the project's `.claude/skills/`, so nothing is overwritten. When a
  name you extract matches one (`ls ${CLAUDE_PLUGIN_ROOT}/skills`), say so in your return: the
  architect leaves a colliding project skill out and reports it on its next run, so the user
  may want to rename it.
- If `docs/architecture.md` already exists, this repo has been planned: say in your return that
  the architect will pick up the new skills on its next `/dev-team:plan-package` run, and that a package
  already planned needs `/dev-team:plan-package <pkg>` re-run for its designers to see them.
