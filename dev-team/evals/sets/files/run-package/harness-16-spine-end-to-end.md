# Harness — run-package eval 16: a package planned with Call paths, built from its contract to its first paths report

Seed: the two-package fixture (`evals/fixtures/two-package/`, through its `reset.sh`) seeded
with the common planning documents and the eval-16 seed
(`evals/sets/files/run-package/seed/common/` then `seed/eval-16/`): a `data` package whose
two sections `ingest` and `sessions` depend on nothing, whose `surface` section depends on
both, and whose contract already carries a **Call paths** heading in the package-contract
template's form — one command, `data-days`, with a file-read path through
`cli.days → pipelines.list_trading_days → ingest.read_trades → open` and a stdout path
`cli.days → print`, every frame a name the contract's **Pipelines** or **Section interfaces**
defines.

The executor is the driver. It follows `skills/run-package/SKILL.md` under its plugin root as
if the user had typed `/dev-team:run-package data`, against its own copy. Agents are spawned
for real in this eval — the scaffold implementer, three designers, three testers, three
implementers, their reviewers and one paths reviewer, with any fix round the reviews cause —
so it costs what a package build costs: expect fifteen to twenty-five agent runs per
configuration. The question is whether the driver, the designers, the tester, the implementers
and the paths reviewer together honour the contract's paths: the surface designed first, from
the contract; every design's §4 carrying skeletons for the frames the paths name; the surface
built last; the paths report comparing the code to the contract. Nothing in it should need the
user.

## Names

- `<plugin>`: the working tree's plugin directory — the one holding this file under
  `evals/sets/files/`, with `.claude-plugin/plugin.json` at its top. Only `reset.sh` and the
  seed are taken from it: a baseline snapshot has no `evals/`.
- `<root>`: the plugin root your prompt names — `<plugin>` for `with_skill`, the baseline
  snapshot's copy of the plugin for `old_skill`. It is `${CLAUDE_PLUGIN_ROOT}` wherever the
  target writes that; substitute it yourself. `status.py` means
  `python3 <root>/skills/status/scripts/status.py`, run from `<copy>`.
- `<copy>`: the fixture copy made below. It is "the repo root" for every step of the target and
  every command you run. It is not the plugin repo, which you never write to: the agents you
  spawn commit in `<copy>`, and the harness's no-commit rule is about the plugin repo.
- `<outputs>`: this run's `outputs/` directory. `<scratchpad>`: your session scratchpad.

## Setup

1. Make your own directory: `mktemp -d` (`mktemp -d <scratchpad>/eval.XXXXXX` when the session
   has a scratchpad). Call it `<tmp>`.
2. `bash <plugin>/evals/fixtures/two-package/reset.sh <tmp>/repo` — the last line printed is
   `<copy>`, on its `build` branch. Never run the plugin inside `<plugin>/evals/fixtures/`.
3. Seed the copy: `cp -R <plugin>/evals/sets/files/run-package/seed/common/. <copy>/` — that
   is `docs/architecture.md`, `docs/packages/data/contract.md` and `docs/sources/trades.md` —
   then the eval-16 seed over it: `cp -R <plugin>/evals/sets/files/run-package/seed/eval-16/.
   <copy>/`, which replaces `docs/architecture.md` (a first slice: `data` covers `load trades`
   and trading sessions) and `docs/packages/data/contract.md` (sections `ingest`, `sessions`,
   `surface`; **Call paths** after **Pipelines**). The probe `docs/sources/trades.md` stays
   the common one: it already serves `data/ingest`, so no PROBE step is due.
4. Commit the seed inside the copy:
   `git -C <copy> add docs && git -C <copy> -c user.name=fixture -c user.email=fixture@example.invalid commit -q -m "fixture: seeded planning documents"`.
   Record `git -C <copy> rev-parse --short HEAD` as `<seed-sha>`.
5. `uv --version` must work (the implementer scaffolds the workspace with it). If it does not,
   say so in `transcript.md` and stop.
6. Work in `<copy>` from here on: `cd <copy> && …` on each call, since your cwd resets between
   calls.

This is fixture setup, not the driver: the driver starts at the target's first step.

## Running the driver

- You are the driver, in this session, exactly as the target describes it: derive state with
  `status.py`, take the ready set, spawn the agents, branch as the target says, end with the
  summary block. The limits the target puts on the driver bind you as it states them: what it
  reads of a return, which files it may open, what it may write in `<copy>`, which git commands
  it may run, which spawn fields come from `status.py --fields`. The read-only copies under
  **After the run** are the one exception, taken after the summary.
- **The scaffold runs for real.** `status.py --scaffold data` prints `scaffold: needed` on the
  fresh copy; spawn the SCAFFOLD implementer as the target says and go on from its return.
- **Spawn agents for real.** One Agent call per spawn, `subagent_type: "dev-team:<agent>"`,
  `run_in_background: false`. **Batch exactly as the target says**: the Agent calls the target
  puts in one message go out together in one assistant message, and the ones it puts in
  separate batches go out in separate messages, with the `status.py` run it prescribes between
  them. Do not merge two batches or split one because of anything in this harness: which rows
  share a batch is part of what this eval measures. The prompt is the target's block for that
  role with every field resolved, plus one line at the top and nothing else changed:
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
2. **The first paths report is written.** The round-1 paths reviewer — the `dev-team:reviewer`
   whose prompt has `Package: data`, `Focus: paths` and `Round: 1` and no `Section:` field —
   has returned. Run the target's re-derive (`status.py data`, whole output, kept in the log),
   send nothing more, and write the summary block the target prescribes for a stop, with
   `stopped because: harness stop — first paths report written`. Whatever that report's
   verdict, no FIX, no second paths round and no close runs in this eval.
3. Fourteen batches of Agent calls have been sent and have returned. Run the target's re-derive
   (`status.py data`, whole output, kept in the log), send nothing more, and write the summary
   block the target prescribes for a stop, with `stopped because: harness stop — fourteen
   batches sent`.

## Answers

None expected. Stated as the user would state them, for a question that comes anyway:

- A `D<n>` a designer or implementer stopped for: the option marked Recommended (the stub's
  `Recommendation:`); recorded in `docs/decisions.md` as the target's Asking step says.
- A review cap, a gate-BLOCKED row, a row that did not move: the user has changed nothing in
  the repo and has nothing to add. *Stop here* where that option is offered; otherwise the
  option marked Recommended, or the first option when none is marked.
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
  with its arguments and full output, and a line between them wherever a batch was sent
  (`batch <n>`), so the order of runs and batches can be read from this file alone;
  `<outputs>/status-final.txt` — `status.py data` run once more.
- `<outputs>/git-log.txt` — `git -C <copy> log --format='%H%n%B' --stat <seed-sha>..HEAD`,
  newest first as git prints it, so the order in which the surface design and each section
  README were committed can be read from it; `<outputs>/git-status.txt` — `git -C <copy>
  status --porcelain`.
- `<outputs>/repo/` — the copy's `docs/`, `tests/` and `packages/` (`rsync -a --exclude .git`),
  so the designs, the reports, the ledgers and the code as the agents left them can be read.
- `<outputs>/returns.md` — one row per agent run: role, `Section:`/`Scaffold:`/`Package:`
  line, and the first line of its last hand-back.
- `transcript.md` — every tool call you made as the driver, in order, each with its tool (Bash,
  Read, Glob, Edit, Write, Agent) and its command or path; what each `status.py` run printed
  (every row's state and its `ready` column); each batch with its calls, whether each was sent,
  and the branch you took on each return; any question and its answer, at the point in that
  order where it happened; where the run ended and why; the final message; then the line
  `--- harness copies ---` and the copies above.
