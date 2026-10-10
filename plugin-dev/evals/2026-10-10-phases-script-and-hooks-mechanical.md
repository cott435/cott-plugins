# `scripts/phases.py` and plugin-dev's two hooks — a plan walked with no model, then each hook in a real session

**Tested against:** uncommitted — see working-tree diff, on `892e3b6` (`scripts/phases.py`, `hooks/hooks.json`, `hooks/guard_agent.py`, `hooks/gate_stop.py`) · model: none for the 37 cases; `claude-sonnet-5-5` (CLI 2.1.283, `--plugin-dir` the working copy) for the two live sessions · 2026-10-10
**Set:** `python3 evals/fixtures/phases/check.py` (37 cases, a throwaway repo it builds) · **Iteration:** none · **Baseline:** none · **Pass rate:** 37/37 cases; both live sessions as expected

## What was tested

That what `run-phases` and `run-phase` used to decide by reading the ledger and the overview
is decided by a script, and that the two hooks act only where they should:

1. `phases.py next`, `brief`, `finish`, `check` and `status` carry a plan from its first
   phase to done: the right phase, the stops (branch, tree), the slice, the ledger row and
   the commit, the refusals when a phase is not whole.
2. `phases.py touch` and `plan-check` hold a plan to the rule that behavioral rows sit only
   in checkpoints and the last phase is one.
3. `hooks/guard_agent.py` refuses an executor or grader spawned through the Agent tool for
   an iteration not laid out `--by-hand`, and nothing else.
4. `hooks/gate_stop.py` blocks, once, the stop of a chat that committed a phase without
   `finish` and left it not standing, and nothing else.

## Method

No model. `check.py` builds a git repo with a two-skill plugin and a four-phase plan
(overview with a `Read|Glob|Grep` cell and a `**Checkpoints:** 3` line, ledger, edit list),
runs `phases.py` as the skills now tell a chat to, and pipes event JSON into the hooks, as
`plugin-anatomy`'s `hooks.md` **How to test it** says. Then the same script on the real
plan, `dev-team`'s determinism (38 phases, 20 done): `next`, `brief`, `status`, `touch
--remaining`, `plan-check --remaining`, and `check 19`.

Then two headless sessions with plugin-dev loaded from the working copy
(`claude -p … --plugin-dir <plugin-dev>`), in a toy plugin directory that had a run-evals
iteration and, for the second, a plan with phase 1 marked begun and committed by hand with
its ledger row left `todo`. The first was told to make one Agent call with an executor's
prompt for that iteration; the second to reply `done` and stop.

## Results

| Case | Observed | Pass |
|---|---|---|
| `next`: the phase on one line; another branch; a stray file | `phase 1 · 01-greet · todo · no behavioral evals · 1 of 4 done`; exit 1 naming both branches; exit 1 listing the path | ✅ |
| `brief`: this phase's rows and notes only, the recurring row, the overview's prose and a `sed` line per other section; marks the phase begun | as expected; a cell holding `` `a|b` `` stays one cell | ✅ |
| `finish` refuses: no note; a log the index does not list; a change outside the plugin not named `--also` | exit 1 naming each; nothing committed | ✅ |
| `finish`: one commit with the subject and trailer, a clean tree, the row `done` with log and notes, phase 0's `(phase 0)` resolved to its SHA | as expected | ✅ |
| `check 1` / `check 2` | exit 0 with the commit / exit 1 naming the commit and the row | ✅ |
| a checkpoint: `finish` with a behavioral row not run; an iteration with no report; a run not run; then whole | exit 1 naming the row, the report, the run; then committed, `next: none` | ✅ |
| `next` when every phase is done; `status` | exit 3; one line per phase, the checkpoint with `evals 3/4, 1.5M tokens` | ✅ |
| `touch`; `plan-check` on the plan as written | hello last touched in 2, evals at 3; `ok` | ✅ |
| `plan-check`: a behavioral row outside a checkpoint; the last phase not one; none named | FAIL each, exit 1; a later touch of the row's target is a warning | ✅ |
| gate: no phase begun; begun and not committed; outside a plugin; unreadable event | exit 0 each, the last with the reason on stderr | ✅ |
| gate: the phase committed by hand, its row not done; the second stop | exit 2 with `is \`todo\`, not \`done\`` and the `finish` command; exit 0 | ✅ |
| gate after `finish` puts it right | exit 0, the mark gone | ✅ |
| guard: an executor, a grader, for a runner's iteration | exit 2 with the `run` command | ✅ |
| guard: the iteration `--by-hand`; any other spawn; a blind comparator; unreadable event | exit 0 each | ✅ |
| the determinism plan: `next`, `status`, `brief` | `phase 20 · 20-write-scope · todo · no behavioral evals · 20 of 38 done`; 38 rows read, three of them with a `|` inside a code span; the brief is 10 KB where the overview and ledger are 127 KB | ✅ |
| the determinism plan: `plan-check --remaining` | `ok: 15 behavioral rows, checkpoints 34, 37`, one warning (curator is touched and has no behavioral row) | ✅ |
| the determinism plan: `check 19` with a later commit on top | exit 1: HEAD is not the phase's commit | ✅ |
| live: an Agent call with an executor's prompt | the tool result is `PreToolUse:Agent hook error: … plugin-dev: an eval's executors and graders are not spawned one Agent call each …` with the `run` command; no subagent started | ✅ |
| live: a chat stopping on a phase committed by hand | after `done`, `Stop hook feedback: … plugin-dev: phase 1 does not stand: the ledger's phase 1 is \`todo\`, not \`done\``; the chat took a second turn quoting it, and its second stop went through (2 turns) | ✅ |

Also run on the edited bundle: `contract_sweep.py` 15/15, `build_site.py` 62 pages exit 0,
`evals/fixtures/run-evals-runner/check.py` 27/27.

## Verdict

The claims held, mechanically and in a live session for each hook: `hooks/hooks.json`
registers from the plugin, `PreToolUse` on `Agent` carries the prompt in
`tool_input.prompt` and exit 2 refuses the spawn, and exit 2 from `Stop` hands the reason
to the chat and lets its next stop through. Still `[unconfirmed]`: the same two events
inside a subagent (`SubagentStop` on a general-purpose phase agent; an Agent call made by a
subagent). No chat has yet run a phase through the rewritten `run-phase` and `run-phases`:
the first phase of the determinism plan run this way is that test, and its log should say
how many turns the phase agent took.
