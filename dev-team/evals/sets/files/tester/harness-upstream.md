# Harness — tester eval 8: a section that consumes an upstream package

Seed: `data` has shipped, and `/dev-team:run-package features` spawned the tester at the TEST
step for `features/returns`, a section with no code yet (`Design mode: new`). The section
consumes `data` through `docs/packages/data/interface.md`. Nobody is at the keyboard, and the
tester asks nothing.

## Answers

- To any question the tester would ask: there is no user, and nobody who knows `data` can be
  asked. Follow the agent file, and say what you did in the return.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo-shipped/`, relative to the plugin directory
  holding this eval set (the one with `.claude-plugin/plugin.json`). The package root is
  `packages/features/`; the tree has nothing there yet. Read the tree; never write into it.
- Three substitutions, for documents the tree does not hold: read
  `evals/sets/files/tester/returns-contract.md` (relative to the plugin directory) as
  `docs/packages/features/contract.md`, `evals/sets/files/tester/returns-design.md` as
  `docs/packages/features/design/returns.md`, and
  `evals/sets/files/tester/returns-data-interface.md` as `docs/packages/data/interface.md`.
- The rest of the repo that the tree does not hold — more of `packages/data/src/`, and the
  environment `.venv/` — is under `evals/sets/files/tester/upstream-env/`, at the same
  repo-relative paths.
- Every file you would write into the repo goes under `outputs/`: a test file or fixture at
  its **package-relative** path (`outputs/tests/intent/returns/<file>.py`), a document at its
  **repo-relative** path (`outputs/docs/…`).
- The commit: `outputs/commit.txt` holds the commit message exactly as it would be given to
  `git commit` — the summary line, a blank line, then the trailer line(s). `outputs/staged.txt`
  lists the paths you would stage, one per line: test files package-relative (`tests/…`),
  documents repo-relative (`docs/…`). No `git` command is needed; none may write. Treat the
  branch as `feature/features` and the baseline as clean; the commit's sha, for the return, is
  `0000000`.
- Running the suite: the Toolchain's one-package test command, pointed at `outputs/`, is
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<repo>/packages/features/src python3 -m pytest
  <outputs>/tests/intent/returns -p no:cacheprovider`, followed by the options the agent file
  gives its test command. `pytest`, `ruff` and `pandas` are available; install nothing. Run
  `ruff format --no-cache` and `ruff check --fix --no-cache` on your `outputs/` tree, never on
  the repo.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness, and the skills the agent file's frontmatter
  preloads are not loaded: invoking or relying on one means reading its `SKILL.md` under the
  plugin directory's `skills/` and recording that in `transcript.md`.
- `transcript.md` records every command exactly as it was run, with its options, and every
  file read, by its path.
