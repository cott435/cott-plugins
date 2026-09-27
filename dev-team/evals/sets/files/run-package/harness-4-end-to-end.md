# Harness — run-package eval 4: the whole two-package build, headless

The executor does not drive anything by hand. It runs the real typed commands headless, in
order, against a fresh fixture copy — the way eval K did — and measures what the streams and
the copy show afterwards. The plugin under test drives itself: `run-package` spawns its agents
inside the `claude -p` process, the hooks fire there, and every commit is the agents' own.

## Names

- `<plugin>`: the plugin directory (the one holding this file under `evals/sets/files/`, with
  `.claude-plugin/plugin.json` at its top). Never modified.
- `<plugin-dir>`: what `--plugin-dir` gets. For `with_skill` it is `<plugin>`. For `old_skill`
  build `<scratchpad>/plugin-baseline`: `cp -R <plugin> <scratchpad>/plugin-baseline`, then
  replace its `skills/run-package/` with the baseline snapshot's `skills/run-package/` (the
  snapshot is the directory the executor prompt names as the baseline's target file's parent),
  and delete `<scratchpad>/plugin-baseline/evals/workspace` if present. Everything but the
  driver is the working tree's in both configurations.
- `<copy>`: `bash <plugin>/evals/fixtures/two-package/reset.sh <scratchpad>/run-package-eval-4-<with_skill|old_skill>`;
  its last printed line. No seeds: `plan-repo` and `plan-package` write the contracts.
- `<outputs>`: this run's `outputs/` directory; make `<outputs>/streams/`.
- `uv --version` and `claude --version` must work; `sqlite3` on PATH. If not, say so in
  `transcript.md` and stop.

## The commands, in order

Each from inside the copy, headless, its stream kept:

```
cd <copy> && claude -p "<command>" --plugin-dir <plugin-dir> --output-format stream-json --verbose --permission-mode bypassPermissions > <outputs>/streams/<n>-<slug>.jsonl 2> <outputs>/streams/<n>-<slug>.stderr
```

| n | command | slug |
|---|---|---|
| 1 | `/dev-team:plan-repo` | `plan-repo` |
| 2 | `/dev-team:plan-package data` | `plan-package-data` |
| 3 | `/dev-team:run-package data` | `run-package-data` |
| 4 | `/dev-team:plan-package analysis` | `plan-package-analysis` |
| 5 | `/dev-team:run-package analysis` | `run-package-analysis` |
| 6 | `/dev-team:finalize-project` | `finalize-project` |

- Run each in the background (a `run-package` takes tens of minutes) and wait for the process
  to exit before starting the next; record start and end times and the exit code in
  `transcript.md`.
- After 3 and after 5, `cd <copy> && python3 <plugin>/skills/status/scripts/status.py <pkg>`
  into `<outputs>/status-data.txt` and `<outputs>/status-analysis.txt`.
- A command that exits non-zero, or whose stream has no final `result` event, is recorded and
  the sequence stops there; write what you have and the summary.
- Headless runs have no `AskUserQuestion`. When a run ends `stopped` on a `D<n>` in
  `<copy>/docs/decisions.md` (a stub with no `Decision:`), act as the user: write the answer
  from **Answers** (or the stub's `Recommendation:`) as `Decision:` and `Status: decided` in the
  file, commit that one file in the copy as `decisions: answer D<n>` (the user's commit, in
  the scratch copy), write the question and answer to `<outputs>/interview.md`, and re-run the
  same command once, keeping its stream as `<n>b-<slug>.jsonl`. Count that re-run's agent runs
  too. A run that stops on a review cap: re-run `/dev-team:run-package <pkg> --defer` once, as
  `<n>c-<slug>.jsonl`, and say so.

## Answers

Stated as the user would state them. Anything not here: the stub's `Recommendation:`.

- Duplicate rows at ingest: *pass them through; `clean` owns deduplication.*
- The rolling VWAP window: *a trade count, default 20, set on the command line; per symbol.*
- Where the report goes: *stdout, as a markdown table; one row per symbol.*
- A configuration or CLI library: *standard library — `os.environ` and `argparse`.*
- A review cap, when asked: *one more round* the first time for a section, *defer* after.

## After the run

- `<outputs>/streams/` — every stream and stderr file, as above.
- `<outputs>/summaries.md` — for each run, the text of its final `result` event, verbatim
  (for 3 and 5 that is the driver's summary block).
- `<outputs>/rows.txt` — the idempotence check. Read `<copy>/docs/packages/data/interface.md`
  (**CLI commands**, **Pipelines**) for the command that ingests and stores, and the table or
  database it writes. From the copy: run it once on `data/trades.csv` into a fresh database
  path, count rows (`sqlite3 <db> 'select count(*) from <table>'`), run it a second time on the
  same input and database, count again, and record both counts plus what the second run
  reported inserting. Write the commands you ran and their output.
- `<outputs>/git-log.txt` — `git -C <copy> log --format='%H%n%B' --stat main..build`;
  `<outputs>/git-status.txt` — `git -C <copy> status --porcelain`.
- `<outputs>/commits.md` — one row per agent run, in order, mapped to its commit. An agent run
  is: every `task_started` event carrying a `subagent_type` in any stream (the driver's
  spawns, and the depth-2 spawns of a forked architect), plus one forked run per typed command
  that forks its agent (`plan-repo`, both `plan-package`s, `finalize-project`), plus your own
  `decisions:` commits marked `user`. Columns: stream, index, role, prompt's first line, commit
  sha or `none` (with why: nothing to apply, or a return other than `done`), the
  `Dev-Team-Run:` trailer.
- `<outputs>/fixed-cost.md` — per role, for every subagent spawn in every stream: the context
  the agent held before doing any work. Read it from the subagent's first `assistant` event
  (the events carrying its `parent_tool_use_id`): `usage.input_tokens +
  usage.cache_creation_input_tokens + usage.cache_read_input_tokens`. If the stream does not
  carry subagent turns, read the first `task_progress` event's `usage.total_tokens` for that
  task, as eval L did; the file says which field it used. One row per spawn, then per role min,
  max and mean, with eval L's means in a column beside: implementer 54,342; tester 39,652;
  reviewer 38,467; architect 38,411; designer 26,055 (`evals/2026-09-19-l-fixed-cost-per-section.md`).
- `<outputs>/repo/` — the copy's `docs/`, `packages/`, `tests/` and root `README.md`
  (`rsync -a --exclude .git`).
- `transcript.md` — each command with its exit code and duration, each user action you took
  (answers, re-runs), how you found the ingest command for `rows.txt`, and the final message.
