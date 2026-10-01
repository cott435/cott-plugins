# Harness — tester eval 7: two open decisions in scope

Seed: `/dev-team:run-package data` spawned the tester at the TEST step for `data/ingest`, a
section with no code yet (`Design mode: new`). `docs/decisions.md` holds two open decisions
whose `Scope:` takes in the section, D2 and D3; the design's Open questions has a line for
each. Nobody is at the keyboard, and the tester asks nothing.

## Answers

- To any question the tester would ask: there is no user, and neither open decision can be
  answered today. Work from the documents, and say what you did in the return.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo/`, relative to the plugin directory holding
  this eval set (the one with `.claude-plugin/plugin.json`). Two substitutions, each in place
  of the copy in the tree: read `evals/sets/files/tester/ingest-decisions.md` (relative to the
  plugin directory) as `docs/packages/data/design/ingest.md`, and
  `evals/sets/files/tester/decisions-binding.md` as `docs/decisions.md`. The package root is
  `packages/data/`. Read the tree; never write into it.
- Every file you would write into the repo goes under `outputs/`: a test file or fixture at
  its **package-relative** path (`outputs/tests/intent/ingest/<file>.py`,
  `outputs/tests/fixtures/polygon.sample.json`), a document at its **repo-relative** path
  (`outputs/docs/…`).
- The commit: `outputs/commit.txt` holds the commit message exactly as it would be given to
  `git commit` — the summary line, a blank line, then the trailer line(s). `outputs/staged.txt`
  lists the paths you would stage, one per line: test files package-relative (`tests/…`),
  documents repo-relative (`docs/…`). No `git` command is needed; none may write. Treat the
  branch as `feature/data` and the baseline as clean; the commit's sha, for the return, is
  `0000000`.
- Running the suite: the Toolchain's one-package test command, pointed at `outputs/`, is
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<repo>/packages/data/src python3 -m pytest
  <outputs>/tests/intent/ingest -p no:cacheprovider`, followed by the options the agent file
  gives its test command. `pytest` and `ruff` are on PATH; install nothing. Run `ruff format
  --no-cache` and `ruff check --fix --no-cache` on your `outputs/` tree, never on the repo.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness, and the skills the agent file's frontmatter
  preloads are not loaded: invoking or relying on one means reading its `SKILL.md` under the
  plugin directory's `skills/` and recording that in `transcript.md`.
- `transcript.md` records every command exactly as it was run, with its options, and every
  file read, by its path.
