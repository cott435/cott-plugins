# Harness — tester eval 4: a delta design over a built section

Seed: the architect wrote the change file `docs/packages/data/changes/page-limit.md` for the
built section `data/ingest`, the designer rewrote the design in `delta` mode, and
`/dev-team:run-package data` spawned the tester at the TEST step with `Design mode: delta`.
The section's code has shipped and already does what the change file describes; its intent
tree exists. Nobody is at the keyboard, and the tester asks nothing.

## Answers

- To any question the tester would ask: there is no user. The change file and the rewritten
  design say what changed; the ledger says what shipped differently and was approved. Assert
  those and say so in the return.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo-delta/`, relative to the plugin directory
  holding this eval set (the one with `.claude-plugin/plugin.json`). The package root is
  `packages/data/`. Read the tree; never write into it.
- The existing intent tree is `packages/data/tests/intent/ingest/`. To edit and run it: copy
  that directory whole into `outputs/tests/intent/ingest/`, and `packages/data/tests/fixtures/`
  whole into `outputs/tests/fixtures/` (the conftest reads its sample from there), and make
  your edits under `outputs/`. Every file you did not change must stay byte-identical to the
  repo's copy — that is how the grader checks the scope of the run.
- Any document you would write goes under `outputs/` at its **repo-relative** path
  (`outputs/docs/packages/data/deviations/ingest.md`); test files at their
  **package-relative** path, as above.
- The commit: `outputs/commit.txt` holds the commit message exactly as it would be given to
  `git commit` — the summary line, a blank line, then the trailer line(s). `outputs/staged.txt`
  lists the paths you would stage, one per line (only the files you changed): test files
  package-relative (`tests/intent/ingest/…`), documents repo-relative (`docs/…`). No `git`
  command is needed; none may write. Treat the branch as `feature/data` and the baseline as
  clean; the commit's sha, for the return, is `0000000`.
- Running the suite: `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<repo>/packages/data/src python3 -m
  pytest <outputs>/tests/intent/ingest -q -p no:cacheprovider`. `pytest` and `ruff` are on
  PATH; install nothing. Run `ruff format --no-cache` and `ruff check --fix --no-cache` on your
  `outputs/` tree, never on the repo.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness: invoking one means reading its `SKILL.md`
  under the plugin directory's `skills/` and recording that in `transcript.md`.
