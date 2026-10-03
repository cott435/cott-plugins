# Harness — run-package eval 19: one section marked as a data stage, walked from nothing to DONE on real data

Seed: the two-package fixture (`evals/fixtures/two-package/`, through its `reset.sh`) seeded by
`evals/sets/files/run-package/seed/eval-19/seed.sh`, which lays the common planning documents
(`seed/common/`) and the eval-19 seed over the copy, one commit per step: a `data` package
planned with four sections — `ingest`, `clean`, `storage`, `surface` — whose workspace is
scaffolded and whose `ingest` section is designed, tested, built and approved in round 1.
The contract's `clean` row depends on `ingest` and is marked as a data stage: its `source` cell
reads `stage:rawtrades`, its `builds with` cell `dev-team:data-quality`, and **Package
conventions** holds the line
`` `stage:rawtrades` — the trade rows ingest reads; lands at data/trades.csv; pull cap 500 rows, D1 ``,
with `D1` decided in `docs/decisions.md`. Nothing of `clean`, `storage` or `surface` exists.
The stage's data is on disk: `data/trades.csv`, the fixture's 400-row export plus nine rows
added after `docs/sources/trades.md` was written and after `ingest` was approved, 409 data
rows in all. Every one of them parses, so `ingest` reads all 409.

The executor is the driver. It follows `skills/run-package/SKILL.md` under its plugin root as
if the user had typed `/dev-team:run-package data clean`, against its own copy. Agents are
spawned for real in this eval, for one section, so it costs what one section's build costs
plus the runs that look at the data: expect eight to fourteen agent runs per configuration.
The question is what the driver does with a row marked this way, from its first `status.py`
run to the section's DONE, and what the agents it spawns leave on disk.

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
2. `uv --version` must work (the seed runs `uv sync`, and the agents run the repo's checks
   with it). If it does not, say so in `transcript.md` and stop.
3. `bash <plugin>/evals/fixtures/two-package/reset.sh <tmp>/repo` — the last line printed is
   `<copy>`, on its `build` branch. Never run the plugin inside `<plugin>/evals/fixtures/`.
4. Seed the copy: `bash <plugin>/evals/sets/files/run-package/seed/eval-19/seed.sh <copy>`.
   It makes seven commits — the planning documents, the workspace (root `pyproject.toml`,
   `uv.lock`, `mkdocs.yml`, `.gitignore`, the package skeleton), `ingest`'s design, its intent
   tests, its code with README and unit tests, its two round-1 reports, and the nine added
   rows of the export — and prints the short sha of the last one. Record it as `<seed-sha>`.
   If the script fails, write its output to `transcript.md` and stop.
5. Work in `<copy>` from here on: `cd <copy> && …` on each call, since your cwd resets between
   calls.

This is fixture setup, not the driver: the driver starts at the target's first step.

## Running the driver

- You are the driver, in this session, exactly as the target describes it: derive state with
  `status.py`, take the ready set, spawn the agents, branch as the target says, end with the
  summary block. The limits the target puts on the driver bind you as it states them: what it
  reads of a return, which files it may open, what it may write in `<copy>`, which git commands
  it may run, which spawn fields come from `status.py`. The read-only copies under **After the
  run** are the one exception, taken after the summary.
- **The workspace is scaffolded.** `status.py --scaffold data` prints `scaffold: done` on the
  seeded copy, so no SCAFFOLD step is due. If it prints anything else, say so in
  `transcript.md` and do what the target says.
- **Spawn agents for real.** One Agent call per spawn, `subagent_type: "dev-team:<agent>"` with
  the agent the target names for the step, `run_in_background: false`. Batch exactly as the
  target says: the Agent calls it puts in one message go out together, and the ones it puts in
  separate batches go out in separate messages, with the `status.py` run it prescribes between
  them. The prompt is the target's block for that role with every field resolved — or, where
  the target says a `status.py` output is the prompt, that output — plus one line at the top
  and nothing else changed:
  `Repo: <copy> — run every command from this directory and resolve every path in this prompt against it; ${CLAUDE_PLUGIN_ROOT} is <root>.`
- If an Agent call fails because the agent type is unknown, write the error to
  `transcript.md`, write the summary block the target prescribes for a stop, and stop: that
  agent is not registered in this session, and that is the result.
- **The decisions sync is run by hand.** The plugin's hooks key on your session's directory,
  not on `<copy>`, so the hook that folds a section's decisions inbox
  (`docs/packages/data/decisions/<section>.md`) into `docs/decisions.md` does not run for an
  agent that works in `<copy>`. After every batch returns, and before the target's re-derive,
  run `cd <copy> && python3 <root>/hooks/sync_decisions.py --all` — the by-hand form that
  script's own header documents — and write what it printed to `transcript.md`. It stands in
  for the hook and is not a step of the driver; run nothing else in its place.
- The stop gate is a hook too, so it may write no record for an agent that works in `<copy>`.
  When it did not, say so in `transcript.md` and go on as the next `status.py data` says; do
  not run a gate yourself.
- No live user. Wherever the target would call `AskUserQuestion`, append one block to
  `<outputs>/interview.md` — the question's text exactly as you would pass it, each option's
  label and description, then the answer — answer from **Answers** below, record the answer
  exactly as the target says to, and continue as the target says.

## Where the run ends

At the first of these:

1. The target ends on its own: the section it was asked for is done, or it stops as it
   prescribes (a stop it names, or a question answered *stop here*). Its own last message is
   the result.
2. Sixteen batches of Agent calls have been sent and have returned. Run the target's re-derive
   (`status.py data`, whole output, kept in the log), send nothing more, and write the summary
   block the target prescribes for a stop, with `stopped because: harness stop — sixteen
   batches sent`.

## Answers

Stated as the user would state them. What the user knows about the export:

- **A row that repeats another row exactly**, all five fields equal: one copy is a real trade
  and the repeat is the export writing it twice. Keep one copy; the repeats are to be removed.
- **A symbol in lowercase** (`aaa`, `bbb`, `ccc`): the same instrument as the uppercase
  symbol; the casing is the export's mistake. The row is a real trade: correct the symbol to
  uppercase and keep it.
- **A price of zero or below**: not a trade the analyst can use, and nobody can say what the
  price should have been. It must not be among the kept rows: remove it.
- **A size of zero**: no units changed hands, so it is not a trade. Remove it.
- **A timestamp earlier than the row before it**: nothing is wrong with the row; the export
  is not in time order. No row is removed or changed for it.
- **Any other kind of row** the user is asked how to treat: the user has no view of their own
  and takes the treatment recommended.

For a question about how one kind of row is to be treated, pick the option that says what the
matching line above says; when no option says it, the option marked Recommended, and note in
`transcript.md` which line you matched and what the options were.

Other questions a run could ask:

- How many rows may be pulled when the data is not on disk (`D1`): the data is on disk and
  nothing needs pulling; 500 rows, as already decided.
- Any other `D<n>` a designer or implementer stopped for: the option marked Recommended (the
  stub's `Recommendation:`), recorded in `docs/decisions.md` as the target's Asking step says.
- Asked whether `data/clean` gets one more round or what is still open is deferred: the user
  does not want the section designed and built again now; what is still open can wait in the
  backlog. *Defer* where that option is offered.
- An agent that returned `blocked`, a review cap, a gate-BLOCKED row, a row that did not move,
  a `spec-change` the target asks about: the user has changed nothing in the repo and has
  nothing to add. *Stop here* where that option is offered; otherwise the option marked
  Recommended, or the first option when none is marked.

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
  with its arguments and full output as the driver's own call printed it, and a line between
  them wherever a batch was sent (`batch <n>`), so the order of runs and batches can be read
  from this file alone. A run that printed a block the driver then sent as a prompt is kept
  whole, every line as printed. `<outputs>/status-final.txt` — `status.py data` run once more.
- `<outputs>/git-log.txt` — `git -C <copy> log --format='%H%n%B' --stat <seed-sha>..HEAD`,
  newest first as git prints it; `<outputs>/git-status.txt` — `git -C <copy> status
  --porcelain`.
- `<outputs>/repo/` — the copy's `docs/`, `packages/` and `data/`
  (`rsync -a --exclude .git --exclude .venv --exclude __pycache__`), so the documents under
  `docs/sources/`, the design, the reports, the ledgers, `docs/decisions.md` and the code as
  the agents left them can be read.
- `<outputs>/stores.txt` — three listings, each under a line naming its command, run from
  `<copy>`: `find .dev-team/data -type f | sort` (with `wc -c` beside each file; `no such
  directory` when it is absent); `git ls-files .dev-team`; and `ls -la rejects` (`no such
  directory` when it is absent).
- `<outputs>/returns.md` — one row per agent run: role, its `Section:` line, its `Mode:` line
  when the prompt has one, and the first line of its last hand-back.
- `transcript.md` — every tool call you made as the driver, in order, each with its tool (Bash,
  Read, Glob, Edit, Write, Agent) and its command or path; what each `status.py` run printed
  (every row's state, evidence and `ready` column); each batch with its calls, whether each was
  sent, and the branch you took on each return; each `sync_decisions.py --all` run and its
  output; any question, its options and its answer, at the point in that order where it
  happened; where the run ended and why; the final message; then the line
  `--- harness copies ---` and the copies above.
