# Harness — tester eval 1: intent tests from a complete design

Seed: `/dev-team:run-package data` spawned the tester at the TEST step for `data/ingest`; the
design is complete, nobody is at the keyboard, and the tester asks nothing.

## Answers

- To any question the tester would ask: there is no user. Take the documents' own assumption
  (`Assumption if unanswered:` in `docs/decisions.md`, the design's Open questions) and say so
  in the return.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo/`, relative to the plugin directory holding
  this eval set (the one with `.claude-plugin/plugin.json`). The package root is
  `packages/data/` under it. Read the tree; never write into it.
- Every file you would write into the repo goes under `outputs/` at its **package-relative**
  path: `outputs/tests/intent/ingest/<file>.py`, `outputs/tests/fixtures/polygon.sample.json`.
- The commit: `outputs/commit.txt` holds the commit message exactly as it would be given to
  `git commit` — the summary line, a blank line, then the trailer line(s). `outputs/staged.txt`
  lists the package-relative paths you would stage, one per line. No `git` command is needed;
  none may write. Treat the branch as `feature/data` and the baseline as clean.
- Running the suite: `PYTHONPATH=<repo>/packages/data/src python3 -m pytest
  <outputs>/tests/intent/ingest -q -p no:cacheprovider`. `pytest` and `ruff` are on PATH;
  install nothing. Run `ruff format` and `ruff check --fix` on your `outputs/` tree, never on
  the repo.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness: invoking one means reading its `SKILL.md`
  under the plugin directory's `skills/` and recording that in `transcript.md`.
