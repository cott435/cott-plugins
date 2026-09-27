# Harness — map-repo eval 1 (two packages, no docs)

What the user wants: the repo adopted into the planning system in one run — one package
contract per package written from its code, the repo contract written from those contracts
and the import graph, and every defect noticed while mapping filed to the backlog.

## The repo

- The repo root is `evals/sets/files/map-repo/two-packages/`, relative to the plugin
  directory holding this eval set (the one with `.claude-plugin/plugin.json`). Treat it as
  the repo and read it read-only. It has no `docs/` directory: nothing is a re-map, and
  every existing contract is `none`.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory (the current working directory).
- The run gate passes. Do not run `status.py --run-gate`; branch and baseline are the
  harness's concern.
- `[tool.importlinter]` is not configured anywhere in the fixture, so `lint-imports` is not
  available: the import graph comes from the read-only grep, over the fixture tree.
- Today's date is the real date.

## What you can and cannot do

- Write every file the run would write under `outputs/`, keeping the repo-relative path:
  `outputs/docs/architecture.md`, `outputs/docs/packages/<pkg>/contract.md`,
  `outputs/docs/followups.md`, and `outputs/docs/decisions.md` if the run stubs a decision.
  Write nothing anywhere in the fixture or the plugin.
- You cannot spawn `dev-team:architect`. Where the run fans out, write into `transcript.md`
  the exact Agent calls you would send — how many, in how many messages, each call's
  `subagent_type`, `run_in_background` and the full prompt — and then carry out each
  spawned architect's task yourself, one after another, as a proxy for it.
- A run that follows the skill file also follows `agents/architect.md` (the agent the skill
  forks into) and the templates that `skills/planning-templates/` names, as that agent would.
  A run without the skill file has no such instructions and does the task as it sees fit.
- Do not commit. State each commit the run would make in `transcript.md`: its scope, its
  message and its trailer.

## Questions

The interview gate should find nothing to ask on this tree: the packages are visible. If
you do ask, write the question and its options to `outputs/interview.md`, take the option
marked Recommended, and continue.
