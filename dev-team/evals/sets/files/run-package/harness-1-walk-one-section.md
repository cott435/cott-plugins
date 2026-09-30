# Harness — run-package eval 1: walk one section to DONE

The executor is the driver. It follows `skills/run-package/SKILL.md` (the working tree's copy
for `with_skill`, the snapshot's for `old_skill`) as if the user had typed
`/dev-team:run-package data ingest`, against a scratch copy of the two-package fixture seeded
with a planned `data` package. Nothing in this eval should ask the user.

## Names

- `<plugin>`: the plugin directory — the one holding this file under `evals/sets/files/`, with
  `.claude-plugin/plugin.json` at its top. It is `${CLAUDE_PLUGIN_ROOT}` wherever the target
  writes that; substitute it yourself. `status.py` means
  `python3 <plugin>/skills/status/scripts/status.py`, run from `<copy>`.
- `<copy>`: the fixture copy made below. It is "the repo root" for every step of the target and
  every command you run. It is not the plugin repo: the agents commit there, and the harness's
  no-commit rule is about the plugin repo, which you never write to.
- `<outputs>`: this run's `outputs/` directory. `<scratchpad>`: your session scratchpad.
- `<snapshot>`: for the `old_skill` configuration only, the baseline snapshot's
  `skills/run-package/SKILL.md` is the target file; `status.py`, the agents and the hooks are
  always the working tree's.

## Before starting

1. `bash <plugin>/evals/fixtures/two-package/reset.sh <scratchpad>/run-package-eval-1-<with_skill|old_skill>`
   — a fresh copy per configuration; the last line printed is `<copy>`. Never run the
   plugin inside `<plugin>/evals/fixtures/`.
2. Seed the copy: `cp -R <plugin>/evals/sets/files/run-package/seed/common/. <copy>/` — that is
   `docs/architecture.md`, `docs/packages/data/contract.md` and `docs/sources/trades.md`, the
   documents `plan-repo` and `plan-package data` would have written, so the run starts at a
   planned package.
3. Commit the seed inside the copy, on its `build` branch:
   `git -C <copy> add docs && git -C <copy> -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: seeded planning documents"`.
   Record `git -C <copy> rev-parse --short HEAD` as `<seed-sha>`. This is fixture setup, not
   the driver: the driver's own git rule starts at step 1 of the target's Loop.
4. `uv --version` must work (the implementer scaffolds the workspace with it). If it does not,
   say so in `transcript.md` and stop.

## Running the driver

- You are the driver, in this session, exactly as the target describes it: derive state with
  `status.py`, take the ready set, spawn the agents, branch on first lines, end with the
  summary block. Run every shell command from `<copy>` (`cd <copy> && …` on each call — your
  cwd resets between calls).
- Spawn agents for real: one Agent call per spawn, `subagent_type: "dev-team:<agent>"`,
  `run_in_background: false`, the Agent calls the target puts in one message sent in one
  message, as the target says.
  The prompt is the target's block for that role with every field resolved, plus one line at
  the top and nothing else changed:
  `Repo: <copy> — run every command from this directory and resolve every path in this prompt against it; ${CLAUDE_PLUGIN_ROOT} is <plugin>.`
- If the first Agent call fails because the agent type is unknown, write the error to
  `transcript.md`, write the summary block the target prescribes for a stop, and stop: the
  plugin's agents are not registered in this session, and that is the result.
- The target's limits on the driver bind you: read a return's first line only (past it only
  where the target says so: a `design-gap` it relays, a `blocked` or `stopped` return it asks
  about); open none of the files the agents wrote; write nothing in
  `<copy>` but `docs/decisions.md`, and only as the target's Asking step says; run no git command
  that writes in `<copy>` — `git rev-parse --short HEAD` and `git rev-list --count` only. The
  read-only copies under **After the run** are the one exception, taken after the summary.
- No live user. Wherever the target would call `AskUserQuestion`, write the question, its
  options and the answer you give to `<outputs>/interview.md` (append; one block per question),
  answer from **Answers** below — or, when a question is not covered, with the option the agent's
  return marks Recommended — record it in `docs/decisions.md` exactly as the target's Asking
  step says, and continue as the target says (re-run `status.py`).
- The walk is the one section named in the command: it ends when `status.py data` shows
  `ingest` DONE, or BLOCKED with nothing left to answer. Do not go on to `clean`, `storage` or
  `surface`; the section argument excludes them.

## Answers

None expected. A question that comes anyway is answered with the Recommended option; a review
cap (one more round, or defer) is answered `one more round` the first time and `defer` after.
Say in `transcript.md` that a question came, since eval 1 expects none.

## After the run

Take these from `<copy>` read-only, after the summary block:

- `<outputs>/summary.md` — your final message, the summary block, verbatim.
- `<outputs>/spawns.md` — one entry per Agent call, in order: index; batch number (calls sent
  in one message share it); `subagent_type`; `run_in_background`; the full prompt block sent;
  the return's first line (the whole return for a `design-gap` or `spec-change`).
- `<outputs>/status-log.txt` — every `status.py` invocation you made, in order, each with its
  full output; `<outputs>/status-final.txt` — `status.py data` run once more at the end.
- `<outputs>/git-log.txt` — `git -C <copy> log --format='%H%n%B' --stat <seed-sha>..HEAD`;
  `<outputs>/git-status.txt` — `git -C <copy> status --porcelain`.
- `<outputs>/repo/` — the copy's `docs/`, `tests/` and `packages/` (`rsync -a --exclude .git`),
  so the grader can read the design, the intent tests, the README, the reports and the ledgers.
- `transcript.md` — each `status.py` run and what its rows said; each spawn with its batch and
  the branch you took on its first line; every file you wrote yourself in `<copy>` (only
  `docs/decisions.md` is allowed, and only when asked); every question and answer; the final
  message.
