# Harness — tester eval 6: two cases under the design's Tests heading

Seed: `/dev-team:run-package data` spawned the tester at the TEST step for `data/ingest`, a
section with no code yet (`Design mode: new`). The design was written before the repo's lint
config and `docs/constraints.md` were set. Nobody is at the keyboard, and the tester asks
nothing.

## Answers

- To any question the tester would ask: there is no user, and the designer cannot be asked what
  a case was meant to prove. Follow the agent file, and say what you did in the return.
- The repo's lint: its `ruff.toml` is not in the fixture tree. It selects `E`, `F`, `B`, `PT`
  and `S`, and its only per-file ignores for `tests/intent/**` are `B017` and `PT011`.
- The machine the suite runs on has no network access and no `DATA_VENDOR_KEY`.

## Where the files and the commit go

- The repo root is `evals/sets/files/tester/repo/`, relative to the plugin directory holding
  this eval set (the one with `.claude-plugin/plugin.json`). One substitution: read
  `evals/sets/files/tester/ingest-unwritable.md` (relative to the plugin directory) as
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
- Running the suite, if you get that far: the Toolchain's one-package test command, pointed at
  `outputs/`, is `PYTHONDONTWRITEBYTECODE=1 PYTHONPATH=<repo>/packages/data/src python3 -m
  pytest <outputs>/tests/intent/ingest -p no:cacheprovider`, followed by the options the agent
  file gives its test command. `pytest` and `ruff` are on PATH; install nothing. Run `ruff
  format --no-cache` and `ruff check --fix --no-cache` on your `outputs/` tree, never on the
  repo.
- `${CLAUDE_PLUGIN_ROOT}` is the plugin directory holding this eval set. The Skill tool may not
  resolve this plugin's skills in this harness, and the skills the agent file's frontmatter
  preloads are not loaded: invoking or relying on one means reading its `SKILL.md` under the
  plugin directory's `skills/` and recording that in `transcript.md`.
- `transcript.md` records every command exactly as it was run, with its options, and every
  file read, by its path.
