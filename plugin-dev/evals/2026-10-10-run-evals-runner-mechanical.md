# `run-evals` runner — `init` reuse and working-tree-only, `run`, `report`, with no model; one real-CLI attempt that hit the weekly limit

**Tested against:** uncommitted — see working-tree diff, on `d153fc1` (`skills/run-evals/scripts/eval_workspace.py`, `skills/run-evals/references/prompts.md`) · model: none (`evals/fixtures/run-evals-runner/fake_claude.py` stands in for `claude -p`); the one real attempt named `claude-sonnet-5-5` and ran no turn · 2026-10-10
**Set:** `python3 evals/fixtures/run-evals-runner/check.py` (27 cases, a throwaway repo it builds) · **Iteration:** none kept · **Baseline:** none · **Pass rate:** 27/27 cases

## What was tested

That `eval_workspace.py` now does the three things the cost of a phased plan's evals turned on
(1,174 subagents and ~2.0B cache-read tokens for 19 phases of `dev-team`'s determinism plan,
48% of it the phase drivers' own turns):

1. **`run`** executes and grades every run a manifest owes as headless sessions and prints one
   report, so the calling chat takes one turn and not one per session.
2. **`init`** reuses a baseline run an earlier iteration finished at the same ref, model and
   inputs, and regrades it without rerunning it when only the expectations changed.
3. **`init --working-tree-only`** starts no baseline executor at all.

## Method

No model. `check.py` builds a git repo holding a one-skill plugin (a committed baseline, an
edited working tree, a two-eval set), sets `RUN_EVALS_CLAUDE` to `fake_claude.py`, and calls
`init`, `run` and `report` as a chat would. The fake reads the prompt the runner passes, writes
what a session given it would leave (an executor: `transcript.md` and an output copied from
the target file it was told to read; a grader: `grading.json`, failing any expectation tagged
for its configuration), prints a stream-json result record with a fixed `usage`, and logs each
call. `FAKE_PLAN` makes chosen runs exit 1 once, exit 1 always, or name the iteration's
`manifest.json` in a tool call.

Then one attempt with the real CLI (2.1.283): a toy plugin in the session scratchpad, `init`
then `run --jobs 2`, two executors.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `init`, first iteration | 4 runs, each with `inputs_hash`; model recorded; snapshot made | as expected | ✅ |
| `run --dry-run` | lists 4 executors and 4 graders, starts nothing | as expected | ✅ |
| `run` | 4 executor and 4 grader sessions, every grader after the last executor, exit 0 | as expected | ✅ |
| sessions | cwd the plugin directory, the manifest's model, `CLAUDECODE` unset, the `--add-dir` scratch exists | as expected | ✅ |
| plugin roots | the baseline executor read the snapshot's target, the other the working tree's | as expected | ✅ |
| `timing.json` | the session's four usage counts summed (4,330); the grader's `timing` copy dropped from `grading.json` | as expected | ✅ |
| report | pass rates per side; the working tree's failed expectation with `baseline: passed`; the expectation only the baseline failed | `3/4 (75.0%) vs 3/4 (75.0%)`, both lines present | ✅ |
| `init --quiet` | path, counts and warnings; no prompt or expectation | as expected | ✅ |
| `init` again | both baselines `reused_from`, no snapshot, grades kept; `run` starts 2 executors and 2 graders | as expected | ✅ |
| expectations changed | baseline outputs reused and graded again: 2 executors, 3 graders | as expected | ✅ |
| prompt changed / harness sheet changed | that eval's baseline runs again / no baseline reused | as expected | ✅ |
| `--model` other / `--no-reuse` | nothing reused | as expected | ✅ |
| manifest with no `inputs_hash` | passed over by default; reused with `--reuse-unhashed` | as expected | ✅ |
| `--working-tree-only` | evals with an earlier baseline reuse it; the new eval has no baseline, no snapshot, a warning naming it; only working-tree executors run; its baseline cell is `—` | as expected | ✅ |
| executor exits 1 once | run again, `attempts: 2` | as expected | ✅ |
| executor names `manifest.json` | thrown away (`void: a tool call named …` in `run.log`), run again | as expected | ✅ |
| executor exits 1 twice | `not-run.json`, no grader for it, exit 1, the report says `not run:` | as expected | ✅ |
| a run not run | never reused by a later `init`; an older finished run of the same eval is | as expected | ✅ |
| `run` again | retries only the run not run, grades it, exit 0; a third `run` starts nothing and prints the report | as expected | ✅ |
| no `claude` on `PATH` | exit 2, points at **Without the runner** | as expected | ✅ |
| real CLI, 2 executors | sessions run, files written, a report with pass counts | both sessions returned a result record with `is_error` and "You've hit your weekly limit · resets Oct 14 at 4am"; the runner retried each once, wrote `not-run.json`, exit 1, and the report shows the error per run (2.9 s) | ❌ not run |

Also run on the edited bundle: `contract_sweep.py` 15/15, `build_site.py` 62 pages exit 0,
`eval_workspace.py validate` on every committed set exit 0.

## Verdict

The script does what the three claims say, against a stand-in. **Not proven: a real session.**
The real attempt shows the command line is accepted and an error record is parsed and reported,
and nothing more. Still open until an account with headroom runs it, as `[unconfirmed]`:

- that `--permission-mode acceptEdits --allowedTools "Bash Read Write Edit Glob Grep Agent
  Skill WebSearch WebFetch"` lets an executor write its run directory and its `--add-dir`
  scratch unattended (`run-phases`' headless mode ran a whole phase under the same two
  flags: `evals/2026-09-29-run-phases.md`, iteration 2);
- that a successful result record's `usage` is the whole session's, subagents included, which
  is what the report's token counts assume;
- that a grader session can read skill-creator's `grader.md` through `--add-dir`.

The first real run to do: any one-eval set, `init --quiet` then `run`, and check `run.log`, the
two `timing.json` files and the report. No behavioral eval of `run-evals`, `run-phase`,
`run-phases` or `plan-phases` was run on this change, for the same reason; their sets hold no
expectation the change contradicts (checked by reading them), and their next run is that
change's regression.
