# Harness — tester eval 2: a design with a gap

Seed: `/dev-team:run-package data` spawned the tester at the TEST step for `data/ingest`; the
design's Module plan is missing a module; nobody is at the keyboard, and the tester asks
nothing.

## Answers

- To any question the tester would ask: there is no user. Do what the agent file says to do
  when a document cannot be tested, and say so in the return.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo/`, relative to the plugin directory holding
  this eval set (the one with `.claude-plugin/plugin.json`). One substitution: read
  `evals/sets/files/tester/ingest-gap.md` (relative to the plugin directory) as
  `docs/packages/data/design/ingest.md`, in place of the copy in the tree. The package root is
  `packages/data/`. Read the tree; never write into it.
- If you do write anything, it goes under `outputs/` at its package-relative path, with the
  commit message in `outputs/commit.txt` and the staged paths in `outputs/staged.txt` — the
  same rule as eval 1. No `git` command is needed; none may write. Treat the branch as
  `feature/data` and the baseline as clean.
- Running the suite, if you get that far: `PYTHONPATH=<repo>/packages/data/src python3 -m
  pytest <outputs>/tests/intent/ingest -q -p no:cacheprovider`. `pytest` and `ruff` are on
  PATH; install nothing.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness: invoking one means reading its `SKILL.md`
  under the plugin directory's `skills/` and recording that in `transcript.md`.
