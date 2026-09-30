# Harness — run-package evals 5 and 6: two independent sections, one batch per step

The executor is the driver. It follows `skills/run-package/SKILL.md` (the working tree's copy
for `with_skill`, the snapshot's for `old_skill`) as if the user had typed the eval's prompt —
`/dev-team:run-package data` for eval 5, `/dev-team:run-package data --serial` for eval 6 —
against a scratch copy of the two-package fixture seeded with a planned `data` package whose
two sections `ingest` and `sessions` depend on nothing, so both are ready together at every
step until `surface`. This is the design's smallest end-to-end slice: the eval is about how the
driver batches two sections that are always ready at once. Nothing in these evals should ask
the user.

## Names

- `<plugin>`: the plugin directory — the one holding this file under `evals/sets/files/`, with
  `.claude-plugin/plugin.json` at its top. It is `${CLAUDE_PLUGIN_ROOT}` wherever the target
  writes that; substitute it yourself. `status.py` means
  `python3 <plugin>/skills/status/scripts/status.py`, run from `<copy>`.
- `<copy>`: the fixture copy made below. It is "the repo root" for every step of the target and
  every command you run. It is not the plugin repo: the agents commit there, and the harness's
  no-commit rule is about the plugin repo, which you never write to.
- `<outputs>`: this run's `outputs/` directory. `<scratchpad>`: your session scratchpad.
- `<n>`: the eval's ID, `5` or `6`.
- `<snapshot>`: for the `old_skill` configuration only, the baseline snapshot's
  `skills/run-package/SKILL.md` is the target file; `status.py`, the agents and the hooks are
  always the working tree's.

## Before starting

1. `bash <plugin>/evals/fixtures/two-package/reset.sh <scratchpad>/run-package-eval-<n>-<with_skill|old_skill>`
   — a fresh copy per eval and configuration; the last line printed is `<copy>`. Never run the
   plugin inside `<plugin>/evals/fixtures/`.
2. Seed the copy: `cp -R <plugin>/evals/sets/files/run-package/seed/common/. <copy>/` — that is
   `docs/architecture.md`, `docs/packages/data/contract.md` and `docs/sources/trades.md` —
   then the eval-5 seed over it:
   `cp -R <plugin>/evals/sets/files/run-package/seed/eval-5/. <copy>/`, which replaces
   `docs/architecture.md` (a first slice: `data` covers `load trades` and trading sessions) and
   `docs/packages/data/contract.md` (sections `ingest`, `sessions`, `surface`). The probe
   `docs/sources/trades.md` stays the common one: it already serves `data/ingest`, so no
   PROBE step is due.
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
  `run_in_background: false`. **Batch exactly as the target says**: the Agent calls the target
  puts in one message go out together in one assistant message, and the ones it puts in
  separate batches go out in separate messages, with the `status.py` run it prescribes between
  them. Do not merge two batches or split one because of anything in this harness: the batch
  shape is what these evals measure. The prompt is the target's block for that role with every
  field resolved, plus one line at the top and nothing else changed:
  `Repo: <copy> — run every command from this directory and resolve every path in this prompt against it; ${CLAUDE_PLUGIN_ROOT} is <plugin>.`
- If the first Agent call fails because the agent type is unknown, write the error to
  `transcript.md`, write the summary block the target prescribes for a stop, and stop: the
  plugin's agents are not registered in this session, and that is the result.
- If the target stops before any spawn — an argument it does not accept, a run gate FAIL —
  record what it printed, verbatim, in `transcript.md` and as `<outputs>/summary.md`, and stop:
  that is the result, and nothing below applies.
- The target's limits on the driver bind you: read a return's first line only (past it only
  where the target says so); open none of the files the agents wrote; write nothing in
  `<copy>` but `docs/decisions.md`, and only as the target's Asking step says; run no git
  command that writes in `<copy>` — `git rev-parse --short HEAD` and `git rev-list --count`
  only. The read-only copies under **After the run** are the one exception, taken after the
  summary.
- No live user. Wherever the target would call `AskUserQuestion`, write the question, its
  options and the answer you give to `<outputs>/interview.md` (append; one block per question),
  answer from **Answers** below, record it in `docs/decisions.md` exactly as the target's
  Asking step says, and continue as the target says (re-run `status.py`).

## Where the walk ends

The command names no section, so the walk is the whole package — but these evals measure only
the two independent sections, and the harness ends the run early:

- **Stop after the batch in which both sections' round-1 reviewers return; do not continue to
  surface.** The `<section>` argument is not used, because it would walk one section alone and
  serialize the two. When the last round-1 reviewer of the second section has returned, run the
  target's re-derive (`status.py data`, whole output, kept in the log), spawn nothing more, and
  write the summary block the target prescribes for a stop: its first line the command's
  arguments as typed, then `stopped at <the row status.py would run next> <its STEP>` (for
  eval 6 the line starts `run-package data --serial:`); `stopped because: harness stop — both
  sections' round-1 reviews returned`; `sections` and `next` from that final `status.py data`.
- If the two sections fall out of step — a `design-gap`, a `spec-change`, a gate that hands
  one back — keep driving as the target says until both sections' round-1 reviewers have
  returned, and say in `transcript.md` where and why they fell out of step.
- The target may stop on its own first (a block with nothing left to answer, a return the
  target routes to **Summary**): then its own summary is the last message, as it prescribes.

## Answers

None expected. A question that comes anyway — a `D<n>` a designer stopped for, or a BLOCKED
row — is answered with the option marked Recommended (the stub's `Recommendation:`). Say in
`transcript.md` that a question came, since these evals expect none. There is no review cap:
the walk ends at round 1.

## After the run

While the driver runs, keep every version of every stop-gate record, with the watcher of
`harness-4-end-to-end.md` (**The commands, in order**) started beside the session and stopped
when it exits, writing `<outputs>/gate-history/`: a later gate run overwrites
`.dev-team/gate/<pkg>/<section>.txt`, and the F4 observation needs both implementers' records
of the one batch.

Take these from `<copy>` read-only, after the summary block:

- `<outputs>/summary.md` — your final message, the summary block, verbatim.
- `<outputs>/spawns.md` — one entry per Agent call, in order: index; batch number (the Agent
  calls of one assistant message share it; a new message is a new batch); `subagent_type`;
  `run_in_background`; the prompt block's `Section:`, `Scaffold:`, `Round:`, `Focus:` and
  `Letter:` lines where it has them; the full prompt block sent; the return's first line (the
  whole return where the target relays it). Between batches, a line naming each `status.py`
  run you made there.
- `<outputs>/status-log.txt` — every `status.py` invocation you made, in order, each with its
  full output; `<outputs>/status-final.txt` — `status.py data` run once more at the end.
- `<outputs>/git-log.txt` — `git -C <copy> log --format='%H%n%B' --stat <seed-sha>..HEAD`;
  `<outputs>/git-status.txt` — `git -C <copy> status --porcelain`.
- `<outputs>/repo/` — the copy's `docs/`, `tests/` and `packages/` (`rsync -a --exclude .git`),
  and its `.dev-team/gate/` and `.dev-team/stop/` when they exist
  (`rsync -a <copy>/.dev-team/gate <copy>/.dev-team/stop <outputs>/repo/.dev-team/`), so the
  grader can read the designs, the reports, the ledgers, the decisions inboxes and the gate
  records. If `<copy>/.dev-team/gate/` does not exist, say so in `transcript.md` — the stop gate
  keys on the hook event's `cwd`, which in a harness session may not be the copy — and create
  nothing in its place.
- `<outputs>/returns.md` — one row per agent run: role, `Section:`/`Scaffold:` line, and the
  first line of its last hand-back (the last `assistant` record with text in its subagent
  transcript).
- `<outputs>/gates.md` — every record version in `<outputs>/gate-history/` and every final
  `.dev-team/gate/<pkg>/<section>.txt`: header verbatim and modification time; then, for the
  batch holding the two section implementers, each one's gate windows (start: the
  implementer's last `assistant` record before the record's modification time; end: the
  modification time) and one line — `F4: overlap observed` naming the pair, `F4: no overlap`,
  or `F4: not observable` with why — worded as eval 4's `gates.md`.
- `transcript.md` — each `status.py` run and what its rows said (every row's state and its
  `ready` column); each batch with its spawns and the branch you took on each first line; every
  file you wrote yourself in `<copy>` (only `docs/decisions.md` is allowed, and only when
  asked); every question and answer; where the walk ended and why; the final message.
