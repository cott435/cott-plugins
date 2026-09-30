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
  its last printed line. No seeds: `plan-repo` and `plan-package` write the contracts. Two
  setup edits, before command 1:
  - **A `repo`-scope pytest row** (2.2 phase 11), so the `SKIPPED` expectation is not
    vacuous: append `| full suite | 0 failures | \`uv run pytest\` | repo |` as the last row of
    the **Floor** table in `<copy>/docs/constraints.md`, and commit that one file in the copy as
    `fixture: a repo-scope pytest row`.
  - **Only `<plugin-dir>` loaded.** When a dev-team plugin is installed and enabled for the
    user, write `<copy>/.claude/settings.json` as
    `{"enabledPlugins": {"dev-team@cott-plugins": false}}` and add `.claude/settings.json` to
    `<copy>/.git/info/exclude`, so the run gate's clean tree holds and the installed copy never
    answers a `/dev-team:` command.
- `<outputs>`: this run's `outputs/` directory; make `<outputs>/streams/`.
- `uv --version` and `claude --version` must work; `sqlite3` on PATH. If not, say so in
  `transcript.md` and stop.

## The commands, in order

Each from inside the copy, headless, its stream kept:

```
cd <copy> && claude -p "<command>" --plugin-dir <plugin-dir> --output-format stream-json --verbose --permission-mode bypassPermissions > <outputs>/streams/<n>-<slug>.jsonl 2> <outputs>/streams/<n>-<slug>.stderr
```

Add `--model <model>` when the eval's operator names one; both configurations use the same.

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
- While each command runs, keep every version of every stop-gate record: a gate run overwrites
  `<copy>/.dev-team/gate/<pkg>/<section>.txt`, so a later round would erase the one the F4
  observation and the gate expectations need. Start this watcher in the background beside each
  command and stop it when the command exits:

  ```
  mkdir -p <outputs>/gate-history && while :; do for f in <copy>/.dev-team/gate/*/*.txt; do [ -f "$f" ] || continue; m=$(stat -c %Y "$f" 2>/dev/null || stat -f %m "$f"); k=$(basename "$(dirname "$f")")-$(basename "$f" .txt)-$m.txt; [ -e "<outputs>/gate-history/$k" ] || cp -p "$f" "<outputs>/gate-history/$k"; done; sleep 1; done
  ```

  The file name carries the record's modification time (epoch seconds), which is when that
  gate run finished writing it. It reads `.dev-team/` only; it writes nothing in the copy.
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
  (`rsync -a --exclude .git`), and its `.dev-team/gate/` and `.dev-team/stop/` when they exist
  (`rsync -a <copy>/.dev-team/gate <copy>/.dev-team/stop <outputs>/repo/.dev-team/`). The
  decisions inboxes (`docs/packages/<pkg>/decisions/<section>.md`), the per-section ledgers and
  the per-section review directories come with `docs/`.
- `<outputs>/batches.md` — for each `run-package` stream (3, 5 and any `b`/`c` re-run), every
  assistant message of the driver (no `parent_tool_use_id`) that holds one or more Agent
  `tool_use` blocks, in order: the batch number; each call's `subagent_type` and its prompt's
  `Section:`, `Scaffold:`, `Package:`, `Spec-change:`, `Round:` and `Letter:` lines where it has
  them; then, verbatim, the output of the last `status.py <pkg>` tool result before that
  message (every row with its state and `ready` column). A batch is the Agent calls of one
  assistant message: two messages in a row are two batches, whatever the wall clock says.
- `<outputs>/agent-bash.md` — every Bash `tool_use` in any stream made by a `dev-team:` agent
  (an event carrying a `parent_tool_use_id`, or the forked architect or documenter of a typed
  command): stream, the agent's role and `Section:`, the command verbatim, and whether its
  `tool_result` shows a hook refused it (quote the refusal). If a stream does not carry
  subagent tool calls, say so for that stream.
- `<outputs>/gates.md` — the F4 observation and the gate records, from `<outputs>/gate-history/`
  and the final `.dev-team/gate/*/*.txt`: one row per record version — path, its header line
  verbatim, the header's stamp, the file's modification time from the history name, and every
  `SKIPPED`, `TIMEOUT` and `ELSEWHERE` line it holds verbatim. Then the hook timing from the
  streams: every event the `run-package` streams carry for a `SubagentStop` hook run (a
  `system` event naming the hook, with whatever start/end or timestamp fields it has), quoted;
  or, when the streams carry none, say so. Then, for every batch in `batches.md` holding two or
  more section implementers, their two gate windows (header stamp to modification time, or the
  stream's hook events when they exist) and one line: `F4: overlap observed` naming the pair,
  `F4: no overlap`, or `F4: not observable` with why. Say which timing source each window used.
- `transcript.md` — each command with its exit code and duration, each user action you took
  (answers, re-runs), how you found the ingest command for `rows.txt`, and the final message.
