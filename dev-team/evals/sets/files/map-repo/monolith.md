# Harness — map-repo eval 2 (a monolith, no packages)

What the user wants: the repo adopted into the planning system. This tree has no
`packages/`, no `docs/`, and one `src/app/` with several subpackages: the run must decide
whether it can list packages or must ask how the monolith splits.

## The repo

- The repo root is `evals/sets/files/map-repo/monolith/`, relative to the plugin directory
  holding this eval set (the one with `.claude-plugin/plugin.json`). Treat it as the repo
  and read it read-only. It has no `docs/` directory, so no `docs/decisions.md` exists yet
  and no split has been decided.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory (the current working directory).
- The run gate passes. Do not run `status.py --run-gate`.
- `[tool.importlinter]` is not configured; the import graph, if needed, is the read-only grep.
- Today's date is the real date.

## What you can and cannot do

- Write every file the run would write under `outputs/`, keeping the repo-relative path
  (`outputs/docs/decisions.md`, and any other `outputs/docs/...` file the run writes). Write
  nothing anywhere in the fixture or the plugin.
- You cannot spawn `dev-team:architect`. If the run fans out, write into `transcript.md`
  the exact Agent calls you would send and carry each one out yourself as a proxy.
- A run that follows the skill file also follows `agents/architect.md` (the agent the skill
  forks into) and the templates that `skills/planning-templates/` names, as that agent would.
  A run without the skill file has no such instructions and does the task as it sees fit.
- Do not commit. State each commit the run would make in `transcript.md`.

## Questions — the split is not answered here

This harness answers no question about how `src/app/` splits into packages. When the run
reaches the point where it would ask the user about the split, that is the run's approval
point: write the question and its options to `outputs/interview.md`, leave every stub
`open`, do NOT pick a Recommended option, do NOT proceed on any assumption, and stop with
the run's final message. The user answers in a later session, not in this one.

Any other question (not about the split): write it to `outputs/interview.md`, take the
option marked Recommended, and continue.
