# Harness — run-package eval 14: every section reviewed, and a command whose pipeline calls a step through a lambda

Seed: state case `paths-e2e` (`evals/fixtures/state-cases/paths-e2e/`), built with
`evals/fixtures/state-cases/build.py`.

The executor is the driver. It follows `skills/run-package/SKILL.md` under its plugin root as
if the user had typed `/dev-team:run-package data`, against its own copy of the state-case
repo: a `data` package whose four sections — `ingest`, `clean`, `storage`, `surface` — are each
built and approved in round 1, whose package `pyproject.toml` declares a command under
`[project.scripts]`, and whose `packages/data/src/data/pipelines/load.py` passes one of its
steps as a lambda. `docs/packages/data/reviews/` holds the four sections' round-1 reports and
nothing else. Agents are spawned for real in this eval. Nothing in it should need the user.

## Names

- `<plugin>`: the working tree's plugin directory — the one holding this file under
  `evals/sets/files/`, with `.claude-plugin/plugin.json` at its top. Only `build.py` is run
  from it: a baseline snapshot has no `evals/`.
- `<root>`: the plugin root your prompt names — `<plugin>` for `with_skill`, the baseline
  snapshot's copy of the plugin for `old_skill`. It is `${CLAUDE_PLUGIN_ROOT}` wherever the
  target writes that; substitute it yourself. `status.py` means
  `python3 <root>/skills/status/scripts/status.py`, run from `<copy>`.
- `<copy>`: the repo built below. It is "the repo root" for every step of the target and every
  command you run. It is not the plugin repo, which you never write to: the agents you spawn
  commit in `<copy>`, and the harness's no-commit rule is about the plugin repo.
- `<outputs>`: this run's `outputs/` directory.

## Setup

1. Make your own directory: `mktemp -d` (`mktemp -d <scratchpad>/eval.XXXXXX` when the session
   has a scratchpad). Call it `<tmp>`.
2. Build the repo, from `<plugin>`:
   `cd <plugin> && python3 evals/fixtures/state-cases/build.py paths-e2e <tmp>/repo`.
   `<copy>` is `<tmp>/repo`, on its `build` branch. If the command fails, write its output to
   `transcript.md` and stop: the case does not exist yet, and that is the result.
3. `printf '.dev-team/\n' >> <copy>/.git/info/exclude`. A scaffolded repo ignores `.dev-team/`
   through its `.gitignore`; a state-case repo has no `.gitignore`.
4. Record `git -C <copy> rev-parse --short HEAD` as `<seed-sha>`.
5. Work in `<copy>` from here on: `cd <copy> && …` on each call, since your cwd resets between
   calls. Never run the target inside `<plugin>/evals/fixtures/`.

This is fixture setup, not the driver: the driver starts at the target's first step.

## Running the driver

- You are the driver, in this session, exactly as the target describes it: derive state with
  `status.py`, take the ready set, spawn the agents, branch as the target says, end with the
  summary block. The limits the target puts on the driver bind you as it states them: what it
  reads of a return, which files it may open, what it may write in `<copy>`, which git commands
  it may run. The read-only copies under **After the run** are the one exception, taken after
  the summary.
- **The workspace is taken as built.** A state-case repo holds documents and stub code, not a
  uv workspace, so `status.py --scaffold data` prints a `scaffold: needed (…)` line, and
  `status.py data` prints the same line under its table. Read that line as `scaffold: done`,
  whatever reason it gives, every time it prints: spawn no SCAFFOLD implementer, and go on.
- **Spawn agents for real.** One Agent call per spawn, `subagent_type: "dev-team:<agent>"`,
  `run_in_background: false`, the calls the target puts in one batch sent in one message. The
  prompt is the target's block for that role with every field resolved, plus one line at the
  top and nothing else changed:
  `Repo: <copy> — run every command from this directory and resolve every path in this prompt against it; ${CLAUDE_PLUGIN_ROOT} is <root>.`
- If the first Agent call fails because the agent type is unknown, write the error to
  `transcript.md`, write the summary block the target prescribes for a stop, and stop: the
  plugin's agents are not registered in this session, and that is the result.
- The plugin's hooks key on your session's directory, not on `<copy>`, so the stop gate may
  write no record for an agent that works in `<copy>`. When it did not, say so in
  `transcript.md` and go on as the next `status.py data` says; do not run a gate yourself.
- No live user. Wherever the target would call `AskUserQuestion`, append one block to
  `<outputs>/interview.md` — the question's text exactly as you would pass it, each option's
  label and description, then the answer — answer from **Answers** below, record the answer
  exactly as the target says to, and continue as the target says.

## Where the run ends

At the first of these:

1. The target ends on its own: its last step is done, or it stops as it prescribes (a stop it
   names, or a question answered *stop here*). Its own last message is the result.
2. The driver builds, for the second time in the run, a reviewer call for the package as a
   whole — a `dev-team:reviewer` call whose prompt names the package in a `Package:` field and
   has no `Section:` field. Write that call to `<outputs>/spawns.md` with its prompt verbatim,
   mark it `recorded, not sent`, send nothing more, and write the summary block the target
   prescribes for a stop, with `stopped because: harness stop — second package review
   recorded`.
3. Six batches of Agent calls have been sent and have returned. Run the target's re-derive
   (`status.py data`, whole output, kept in the log), send nothing more, and write the summary
   block the target prescribes for a stop, with `stopped because: harness stop — six batches
   sent`.

## Answers

None expected. Stated as the user would state them, for a question that comes anyway:

- Whatever the driver asks in this run: the user has changed nothing in the repo and has
  nothing to add. *Stop here* where that option is offered; otherwise the option marked
  Recommended, or the first option when none is marked.
- Say in `transcript.md` that a question came.

## After the run

The driver's own output, written as it happens:

- `<outputs>/spawns.md` — one entry per Agent call, in order: index; batch number (the calls of
  one assistant message share it); `subagent_type`; `run_in_background`; the full prompt,
  verbatim, in a fenced block, with its line breaks as sent; `sent` or `recorded, not sent`;
  and for a call that was sent, the first line of its return.
- `<outputs>/interview.md` — one block per question, as above. No question: no file.
- `<outputs>/summary.md` — the driver's final message, verbatim and whole.

Then, after the final message, read-only copies from `<copy>`. These are the harness's, not
the driver's:

- `<outputs>/status-log.txt` — every `status.py` invocation the driver made, in order, each
  with its arguments and full output, and a line between them wherever a batch was sent or
  recorded (`batch <n>`), so the order of runs and batches can be read from this file alone;
  `<outputs>/status-final.txt` — `status.py data` run once more.
- `<outputs>/git-log.txt` — `git -C <copy> log --format='%H%n%B' --stat <seed-sha>..HEAD`;
  `<outputs>/git-status.txt` — `git -C <copy> status --porcelain`.
- `<outputs>/repo/` — the copy's `docs/`, `tests/` and `packages/` (`rsync -a --exclude .git`),
  so the reports, the ledgers and the code as the agents left them can be read.
- `transcript.md` — every tool call you made as the driver, in order, each with its tool (Bash,
  Read, Glob, Edit, Write, Agent) and its command or path; what each `status.py` run printed;
  each batch with its calls, whether each was sent, and the branch you took on each return;
  any question and its answer, at the point in that order where it happened; the final
  message; then the line `--- harness copies ---` and the copies above.
