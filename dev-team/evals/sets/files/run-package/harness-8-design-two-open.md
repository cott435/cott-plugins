# Harness — run-package eval 8: a section with two open design spec-changes

Seed: state case `design-spec-change-two-open`
(`evals/fixtures/state-cases/design-spec-change-two-open/`), built with
`evals/fixtures/state-cases/build.py`.

The executor is the driver. It follows `skills/run-package/SKILL.md` under its plugin root as
if the user had typed `/dev-team:run-package data`, against its own copy of the state-case
repo: a planned `data` package whose `ingest` section has a design and intent tests, and whose
ledger `docs/packages/data/deviations/ingest.md` holds two `spec-change:design` entries, both
`Status: open`. `clean`, `storage` and `surface` have no design. Nothing in this eval should
need the user.

## Names

- `<plugin>`: the working tree's plugin directory — the one holding this file under
  `evals/sets/files/`, with `.claude-plugin/plugin.json` at its top. Only `build.py` is run
  from it: a baseline snapshot has no `evals/`.
- `<root>`: the plugin root your prompt names — `<plugin>` for `with_skill`, the baseline
  snapshot's copy of the plugin for `old_skill`. It is `${CLAUDE_PLUGIN_ROOT}` wherever the
  target writes that; substitute it yourself. `status.py` means
  `python3 <root>/skills/status/scripts/status.py`, run from `<copy>`.
- `<copy>`: the repo built below. It is "the repo root" for every step of the target and every
  command you run. It is not the plugin repo, which you never write to: an agent you spawn
  commits in `<copy>`.
- `<outputs>`: this run's `outputs/` directory.

## Setup

1. Make your own directory: `mktemp -d` (`mktemp -d <scratchpad>/eval.XXXXXX` when the session
   has a scratchpad). Call it `<tmp>`.
2. Build the repo, from `<plugin>`:
   `cd <plugin> && python3 evals/fixtures/state-cases/build.py design-spec-change-two-open <tmp>/repo`.
   `<copy>` is `<tmp>/repo`, on its `build` branch. If the command fails, write its output to
   `transcript.md` and stop: the case does not exist yet, and that is the result.
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
- **Agent calls.** Build each call as the target says: `subagent_type: "dev-team:<agent>"`,
  `run_in_background: false`, the prompt the target's block for that role with every field
  resolved, and the calls the target puts in one batch together in one message. A call you
  send carries one line added at the top of its prompt and nothing else changed:
  `Repo: <copy> — run every command from this directory and resolve every path in this prompt against it; ${CLAUDE_PLUGIN_ROOT} is <root>.`
- **A call may be recorded and not awaited.** If your session cannot spawn the agent — it has
  no Agent tool, or the call fails because `dev-team:designer` (or whichever type the call
  names) is unknown — do not stop as the target's unknown-agent rule says: write the call to
  `<outputs>/spawns.md` with its `subagent_type` and its prompt verbatim, mark it `recorded,
  not sent`, and go on to **Where the run ends**.
- No live user. Wherever the target would call `AskUserQuestion`, append one block to
  `<outputs>/interview.md` — the question's text exactly as you would pass it, each option's
  label and description, then the answer — answer from **Answers** below, and continue as the
  target says.

## Where the run ends

The run ends with the first batch of Agent calls. When every call of that batch has returned,
or has been recorded, run the target's re-derive (`status.py data`, whole output, kept in the
log), spawn nothing more, and write the summary block the target prescribes for a stop, with
`stopped because: harness stop — first batch sent`. If the target stops on its own before any
Agent call, its own last message is the result.

## Answers

None expected. A question that comes anyway is answered with the option marked Recommended, or
the first option when none is marked. Say in `transcript.md` that it came.

## Outputs

The driver's own output, written as it happens:

- `<outputs>/spawns.md` — one entry per Agent call, in order: index; batch number (the calls of
  one assistant message share it); `subagent_type`; `run_in_background`; the full prompt,
  verbatim, in a fenced block, with its line breaks as sent; `sent` or `recorded, not sent`;
  and for a call that was sent, the first line of its return. When the driver made no Agent
  call, the one line `no Agent call`.
- `<outputs>/interview.md` — one block per question, as above. No question: no file.
- `<outputs>/summary.md` — the driver's final message, verbatim and whole.

Then, after the final message, read-only copies from `<copy>`. These are the harness's, not
the driver's:

- `<outputs>/status-log.txt` — every `status.py` invocation the driver made, in order, each
  with its arguments and full output; `<outputs>/status-final.txt` — `status.py data` run once
  more.
- `<outputs>/git-status.txt` — `git -C <copy> status --porcelain`;
  `<outputs>/git-log.txt` — `git -C <copy> log --format='%h %s'`.
- `transcript.md` — every tool call you made as the driver, in order, each with its tool (Bash,
  Read, Glob, Edit, Write, Agent) and its command or path; what each `status.py` run printed;
  each batch with its calls and whether each was sent; any question and its answer, at the
  point in that order where it happened; the final message; then the line
  `--- harness copies ---` and the copies above.
