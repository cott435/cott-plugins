# Harness — tester eval 9: the surface section, tested right after PLAN

Seed: `/dev-team:plan-package data` has just finished, and the contract has **Call paths**, so
`status.py` marks the `surface` row ready at DESIGN and TEST right after PLAN. The surface
designer has returned `done`; `/dev-team:run-package data` now spawns the tester at the TEST
step for `data/surface` (`Design mode: new`). No sibling section has been designed or built,
no sibling README exists (`Dependency READMEs: none`, the `dependency readmes:` line of
`status.py --fields`), and `docs/packages/data/interface.md` does not exist. Nobody is at the
keyboard, and the tester asks nothing.

## Answers

- To any question the tester would ask: there is no user, and nobody who knows `ingest` or
  `clean` can be asked. Follow the agent file, and say what you did in the return.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo/`, relative to the plugin directory holding
  this eval set (the one with `.claude-plugin/plugin.json`). The package root is
  `packages/data/`. Read the tree; never write into it.
- Two substitutions, each in place of the copy in the tree: read
  `evals/sets/files/tester/surface-contract.md` (relative to the plugin directory) as
  `docs/packages/data/contract.md`, and `evals/sets/files/tester/surface-design.md` as
  `docs/packages/data/design/surface.md`, a file the tree does not hold.
- Every file you would write into the repo goes under `outputs/`: a test file or fixture at
  its **package-relative** path (`outputs/tests/intent/surface/<file>.py`), a document at its
  **repo-relative** path (`outputs/docs/…`).
- The commit: `outputs/commit.txt` holds the commit message exactly as it would be given to
  `git commit` — the summary line, a blank line, then the trailer line(s). `outputs/staged.txt`
  lists the paths you would stage, one per line: test files package-relative (`tests/…`),
  documents repo-relative (`docs/…`). No `git` command is needed; none may write. Treat the
  branch as `feature/data` and the baseline as clean; the commit's sha, for the return, is
  `0000000`.
- Running the suite: the Toolchain's one-package test command, pointed at `outputs/`, is
  `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<repo>/packages/data/src python3 -m pytest
  <outputs>/tests/intent/surface -p no:cacheprovider`, followed by the options the agent file
  gives its test command. `pytest`, `ruff` and `pandas` are available; install nothing. Run
  `ruff format --no-cache` and `ruff check --fix --no-cache` on your `outputs/` tree, never on
  the repo.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness, and the skills the agent file's frontmatter
  preloads are not loaded: invoking or relying on one means reading its `SKILL.md` under the
  plugin directory's `skills/` and recording that in `transcript.md`.
- `transcript.md` records every command exactly as it was run, with its options, and every
  file read, by its path.
