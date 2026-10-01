# Harness — run-package eval 9: the user types a sentence where a choice was offered

Seed: state case `blocked-decision` (`evals/fixtures/state-cases/blocked-decision/`), built
with `evals/fixtures/state-cases/build.py`.

The executor is the driver. It follows `skills/run-package/SKILL.md` under its plugin root as
if the user had typed `/dev-team:run-package data`, against its own copy of the state-case
repo: a planned `data` package with no design for any section, and a `docs/decisions.md`
holding three open decisions — `D3` scoped to `data/ingest`, `D4` to `data/clean`, `D5` to
`data/storage` with an assumption to work from.

## Names

- `<plugin>`: the working tree's plugin directory — the one holding this file under
  `evals/sets/files/`, with `.claude-plugin/plugin.json` at its top. Only `build.py` is run
  from it: a baseline snapshot has no `evals/`.
- `<root>`: the plugin root your prompt names — `<plugin>` for `with_skill`, the baseline
  snapshot's copy of the plugin for `old_skill`. It is `${CLAUDE_PLUGIN_ROOT}` wherever the
  target writes that; substitute it yourself. `status.py` means
  `python3 <root>/skills/status/scripts/status.py`, run from `<copy>`.
- `<copy>`: the repo built below. It is "the repo root" for every step of the target and every
  command you run. It is not the plugin repo, which you never write to.
- `<outputs>`: this run's `outputs/` directory.

## Setup

1. Make your own directory: `mktemp -d` (`mktemp -d <scratchpad>/eval.XXXXXX` when the session
   has a scratchpad). Call it `<tmp>`.
2. Build the repo, from `<plugin>`:
   `cd <plugin> && python3 evals/fixtures/state-cases/build.py blocked-decision <tmp>/repo`.
   `<copy>` is `<tmp>/repo`, on its `build` branch. If the command fails, write its output to
   `transcript.md` and stop.
3. `printf '.dev-team/\n' >> <copy>/.git/info/exclude`. A scaffolded repo ignores `.dev-team/`
   through its `.gitignore`; a state-case repo has no `.gitignore`.
4. Work in `<copy>` from here on: `cd <copy> && …` on each call, since your cwd resets between
   calls. Never run the target inside `<plugin>/evals/fixtures/`.

This is fixture setup, not the driver: the driver starts at the target's first step.

## Running the driver

- You are the driver, in this session, exactly as the target describes it, and the limits the
  target puts on the driver bind you as it states them.
- **The workspace is taken as built.** A state-case repo holds documents and stub code, not a
  uv workspace, so `status.py --scaffold data` prints `scaffold: needed (no root
  pyproject.toml)` in every one of them, and `status.py data` prints the same line under its
  table. Read that line as `scaffold: done`: spawn no SCAFFOLD implementer, and go on.
- **No agent is run in this eval.** The repo has no workspace for one to work in. An Agent call
  the driver makes is written to `<outputs>/spawns.md` and not sent, and the run ends at that
  batch: write the summary block the target prescribes for a stop, with `stopped because:
  harness stop — this eval runs no agent`.
- No live user. Wherever the target would call `AskUserQuestion`, append one block to
  `<outputs>/interview.md` — the question's text exactly as you would pass it, each option's
  label and description, then the answer — answer from **Answers** below, and continue as the
  target says. An answer the user typed is what `AskUserQuestion` would hand back for text
  typed in its free-text field: that text, with no option selected.

## Answers

Stated as the user would state them.

- **The first question the driver asks about an open decision.** The user picks none of the
  options. They type, in the free-text field:

  `Tell me what is wrong with dev-team that causes this`

  That sentence is the whole answer. The user says nothing more in this run.
- Any question after that one: the option marked Recommended, or the first option when none is
  marked.

## Outputs

The driver's own output, written as it happens:

- `<outputs>/interview.md` — one block per question, as above. No question: no file.
- `<outputs>/spawns.md` — one entry per Agent call, in order: index; batch number (the calls of
  one assistant message share it); `subagent_type`; `run_in_background`; the full prompt,
  verbatim, in a fenced block; `recorded, not sent`. When the driver made no Agent call, the
  one line `no Agent call`.
- `<outputs>/summary.md` — the driver's final message, verbatim and whole.

Then, after the final message, read-only copies from `<copy>`. These are the harness's, not
the driver's:

- `<outputs>/status-log.txt` — every `status.py` invocation the driver made, in order, each
  with its arguments and full output; `<outputs>/status-final.txt` — `status.py data` run once
  more.
- `<outputs>/git-status.txt` — `git -C <copy> status --porcelain`;
  `<outputs>/git-log.txt` — `git -C <copy> log --format='%h %s'`.
- `<outputs>/decisions.md` — a copy of `<copy>/docs/decisions.md` as the run left it.
- `transcript.md` — every tool call you made as the driver, in order, each with its tool (Bash,
  Read, Glob, Edit, Write, Agent) and its command or path, a file under `<root>` or `<plugin>`
  named as such; what each `status.py` run printed; each question, its options and the answer,
  at the point in that order where it happened; the final message; then the line
  `--- harness copies ---` and the copies above.
