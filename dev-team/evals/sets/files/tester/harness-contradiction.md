# Harness — tester eval 5: a design that contradicts itself

Seed: `/dev-team:run-package data` spawned the tester at the TEST step for `data/ingest`, a
section with no code yet (`Design mode: new`); the design's §4 Workflow and §5 Interfaces
disagree on one item. Nobody is at the keyboard, and the tester asks nothing.

## Answers

- To any question the tester would ask: there is no user, and nobody can say which of the two
  items the designer meant. Do what the agent file says to do with a design that cannot be
  tested as written, and say so in the return.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo/`, relative to the plugin directory holding
  this eval set (the one with `.claude-plugin/plugin.json`). One substitution: read
  `evals/sets/files/tester/ingest-contradiction.md` (relative to the plugin directory) as
  `docs/packages/data/design/ingest.md`, in place of the copy in the tree. The package root is
  `packages/data/`. Read the tree; never write into it.
- Every file you would write goes under `outputs/`: a document at its **repo-relative** path
  (`outputs/docs/packages/data/deviations/ingest.md`), a test file at its
  **package-relative** path (`outputs/tests/intent/ingest/<file>.py`).
- The commit: `outputs/commit.txt` holds the commit message exactly as it would be given to
  `git commit` — the summary line, a blank line, then the trailer line(s). `outputs/staged.txt`
  lists the paths you would stage, one per line: documents repo-relative (`docs/…`), test
  files package-relative (`tests/…`). No `git` command is needed; none may write. Treat the
  branch as `feature/data` and the baseline as clean; the commit's sha, for the return, is
  `0000000`.
- Running the suite, if you get that far: `PYTHONDONTWRITEBYTECODE=1
  PYTHONPATH=<repo>/packages/data/src python3 -m pytest <outputs>/tests/intent/ingest -q -p
  no:cacheprovider`. `pytest` and `ruff` are on PATH; install nothing.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness: invoking one means reading its `SKILL.md`
  under the plugin directory's `skills/` and recording that in `transcript.md`.
