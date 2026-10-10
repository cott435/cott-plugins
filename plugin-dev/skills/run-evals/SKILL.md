---
name: run-evals
description: Use when the user wants to test, prove, benchmark, or verify the behavior of a specific skill or agent that lives in a Claude Code plugin repo — e.g. "run the evals for this skill", "run eval N against the baseline", "does this agent still do X after my edit?", "benchmark this skill against main/the previous version", "prove it before I claim that", "check whether the description triggers". Covers running a target's committed eval set (evals/sets/{target}.json), comparing the working-tree version against a baseline ref, grading each assertion, opening the benchmark/viewer for review, trigger-rate tests, and logging the result. Use it whether the user names the set file, the target, the plugin directory, or just asks to test behavior after a change. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json); not for application test suites, generic eval harnesses for models, or creating a new skill from scratch.
---

# Running a target's evals

An eval is a claim about how one skill or agent behaves, checked the same way every time
and kept where the next change can rerun it. This skill runs one target's evals from its
committed set, stops for the user to look at the outputs, and hands the result to
`log-eval`. The grader, benchmark and viewer are skill-creator's — see
`references/skill-creator.md` for finding them and the layout they expect.

`S` below is `${CLAUDE_SKILL_DIR}/scripts/eval_workspace.py`. Run everything from the
plugin's own directory.

## What a run is

One target (a skill or an agent), one set file, one iteration. A run starts from
`evals/sets/<target>.json`. A test that is not in a set is added to it first — with its
`added_in` saying which change added it — so a later change to the same target can rerun
it as a regression check. A test run only in a chat is a test nobody can repeat.

A run costs model time on three things: an executor per configuration per eval, a grader per
run, and every turn the chat that drives them takes while it waits. This skill spends on the
first only where the answer is not already on disk, and keeps the third near zero: the runs
are headless sessions a script starts and waits for, and the chat reads one report.

## The kinds

Five kinds, each defined with its method in `references/eval-kinds.md`: `mechanical`,
`load`, `behavioral`, `trigger`, `platform-fact`.

Within one run the order is mechanical, then load, then trigger, then behavioral. A failing
mechanical check stops the run: a bundle that does not pass its own checks makes behavioral
results meaningless, so fix it first. Trigger comes before behavioral because the two do not
depend on each other except in one direction: `run_loop` may rewrite the target's
`description:`, and behavioral runs read the working-tree file, so a description applied
after the behavioral run leaves its results graded against a file that no longer exists. `platform-fact` evals are not part of a target's run;
a plan runs them once, before anything depends on them.

## The set

`evals/sets/<target>.json`, committed. The shape:

```json
{
  "target": "design-plugin",
  "target_path": "skills/design-plugin/SKILL.md",
  "evals": [
    {
      "id": 1,
      "name": "trading-research-three-jobs",
      "kind": "behavioral",
      "baseline": "previous",
      "harness": "evals/sets/files/design-plugin/trading.md",
      "prompt": "/plugin-dev:design-plugin --new trading-agents a plugin for stock research agents",
      "expected_output": "one sentence a reviewer can hold the output against",
      "files": [],
      "expectations": ["an observable statement about outputs/ or transcript.md"],
      "added_in": "0.9-evals phase 0"
    }
  ]
}
```

- `baseline` is `none` (a new target — the baseline runs without it), `previous` (the plugin
  as of the commit the current work started from: `git merge-base HEAD <default branch>`
  when on another branch, otherwise HEAD, the parent of uncommitted work), or an explicit git
  ref. `references/eval-kinds.md` **Baselines** says where the default branch is looked for
  and what `S init` warns about.
- `harness` is optional, and required for a target that asks the user anything: a file of
  scripted answers the executor uses in place of the user.
- Every expectation is observable in `outputs/` or `transcript.md` — a file exists, contains
  a thing, a count is under a limit, the chat message does or does not do something. "Is
  good quality" is not an expectation. One that can only be checked in the transcript —
  what was read, asked, run or said — names `transcript.md`: that word is how `S blind`
  knows to withhold it from a comparator, which sees `outputs/` only.
- `"runs": N` on an eval runs each configuration N times; the default is one.
- Paths are relative to the plugin directory.

`python3 S validate evals/sets/<target>.json` enforces the shape and exits 1 naming each
problem as `path: eval <id>: <problem>`. It accepts a `target_path` that does not exist yet —
a plan writes a new target's set in phase 0, before the phase that creates the target —
and `S init` refuses one, since there is nothing to run.

## The workspace

`evals/workspace/<target>/iteration-N/`, gitignored, never under `skills/` —
skill-creator's default `<skill>-workspace/` sibling would be picked up by
`check-contracts`' `skills/*` globs and by `build-site`. The layout, which `S init` creates:

```
evals/workspace/<target>/iteration-N/
├── manifest.json                        what `S init` wrote
├── baseline-snapshot/                   git archive of the whole plugin, minus evals/, at the
│                                        baseline ref — only when a baseline runs here
├── eval-<id>-<name>/
│   ├── eval_metadata.json               {eval_id, eval_name, prompt, assertions}
│   ├── with_skill/
│   │   ├── eval_metadata.json           same file again — the viewer reads it here
│   │   └── run-1/{outputs/, transcript.md, grading.json, timing.json, session.jsonl}
│   └── old_skill/ | without_skill/      same shape; absent in a working-tree-only iteration
│                                        with no earlier run to reuse
├── run.log, report.md, run-summary.json `S run`: one line per session, then the report
├── benchmark.json, benchmark.md         aggregate_benchmark.py, for the viewer
└── feedback.json                        the viewer, after review
```

`with_skill` is the target as it is in the working tree. The baseline is `old_skill` (a
snapshot at a ref) or `without_skill` (`baseline: none`). These are skill-creator's names;
agents use them too, since its benchmark labels configurations by them. Iterations are kept:
the next one is compared against the last, and reuses its baseline runs.

## The model

Every session this skill starts — executor, grader, comparator — runs on Sonnet 5.5, unless
the user names another model for the run. `S init --model <full ID>` records it in the
manifest and `S run` passes it on; the default is `claude-sonnet-5-5`, the full ID, since
`--model sonnet` is Sonnet 5 in a headless session (`plugin-anatomy`'s
`references/agents.md`, **Model names**). In the Agent tool it is `model: "sonnet"`. The log
names the model each kind of session ran on.

## What runs, and what is reused

A baseline at a fixed ref is the same plugin every time, so its run is the same run. `S init`
looks through the target's earlier iterations for a finished baseline run of each eval at the
same ref, on the same model, with the same inputs (the prompt, the harness sheet and every
path under `files`, as a digest in the manifest's `inputs_hash`). A hit is copied into the new
iteration whole and marked `reused_from`; no executor runs for it. When the eval's
expectations have changed since, its outputs are kept and its `grading.json` is dropped, so it
is graded again and not run again. `--no-reuse` runs every baseline regardless.

Two ways to run a set's evals, from the phase note's **Baseline** cell or the request:

- **Compared** — the default. Both configurations, the baseline reused where there is one
  and run where there is not. For an eval being run for the first time, whose point is that
  the baseline fails something the working tree passes.
- **Working tree only** — `S init --working-tree-only`, for a row whose Baseline cell says
  `working tree only`: a regression check on evals that already passed. No baseline executor
  is ever started. A baseline an earlier iteration finished is still reused, so the report
  has its column for free; an eval with none goes without. The question such a row asks is
  "does it still pass", which needs no second side — until an expectation fails. Then that
  eval alone is run again compared (`S init … --evals <id>`), which costs one baseline
  executor at most, and the report says whether the baseline fails it too.

## The behavioral loop

1. `python3 S validate evals/sets/<target>.json`
2. `python3 S init . <target> --quiet [--evals 1,2,3] [--baseline REF]
   [--working-tree-only]` — writes `manifest.json` in the new iteration (the baseline ref,
   the model, the skill-creator directory or null, and one entry per run with `run_dir`,
   `outputs_dir`, `prompt`, `harness`, `target_file`, `plugin_root`, `expectations`,
   `inputs_hash` and `reused_from`) and, with `--quiet`, prints only what this chat needs:
   the iteration path, how many executors will run, how many baseline runs were reused, and
   `warnings`. The manifest is the runner's input; without `--quiet` it is printed whole,
   expectations and all. A warning is also printed to stderr. Settle each one before running
   anything: a baseline that fell back to HEAD, or one identical to the working tree,
   compares the target with itself — rerun `init` with `--baseline <ref>` unless the user
   says the baseline is right.
3. `python3 S run <iteration>`, as **one background command**, and wait for it to exit.
   When several targets run in one phase, `init` them all first and start their `run`
   commands together. It starts every executor the manifest still owes as a headless
   `claude -p` session in the plugin directory, at most `--jobs` at once (default 6), with
   the prompt in `references/prompts.md`; then, once every executor has finished, one grader
   per run that has no grades; then it prints the report. Do not poll it and do not read
   `run.log` while it runs: each look is a turn that re-reads this whole chat.
   **An executor ended by an error is run once more**, by the runner: a session that ends on
   an API error (a dropped connection, an overload, a refusal) or that named a file its
   expectations are in has no result — its outputs are emptied, its transcript deleted, and
   the same prompt runs again. A second failure leaves `not-run.json` in the run directory:
   the run is recorded as not run, is left out of the pass rate, and the log names it and
   the error. Partial outputs are never graded. `run` exits 1 when any run was not run or
   not graded, and running it again retries exactly those.
4. Read the report it printed (also `<iteration>/report.md`), and nothing else under the
   iteration unless the report sends you there. It holds the table of pass counts per eval
   and side, the pass rates, each expectation the working tree failed with the grader's
   evidence and what the baseline did with the same expectation, the expectations only the
   baseline failed, the graders' remarks on the expectations themselves, and the cost. A
   failed expectation the evidence does not settle is the one reason to open a run's
   `transcript.md` or `outputs/` — that run's, not every run's.
5. For a working-tree-only iteration with a failed expectation whose baseline is `not run`:
   `S init … --evals <those ids>` without the flag, `S run`, and read that report.
6. The graders' remarks: an expectation one calls trivially satisfied, or an outcome it says
   nothing checks, is rewritten or added in the set, in this change.
7. The viewer, when a person is going to review (see **Review**).

The executor and grader prompts are `references/prompts.md`, the one copy; what each harness
rule is for is `references/eval-kinds.md`, **Harness rules**. `manifest.json` and both copies
of `eval_metadata.json` hold the expectations, and `evals/sets/` holds them too. No executor
may read any of them; the prompt says so, and the runner throws away a run whose tool calls
named one.

## Review

First, from the skill-creator directory, the benchmark the viewer shows:
`python3 -m scripts.aggregate_benchmark <iteration-dir> --skill-name <target>`. A 0% row
means check the tree before believing it. Its Delta column is the first configuration
alphabetically minus the second, so against `old_skill` the sign is inverted — read the two
rows, not the delta. `S run` has already dropped the `timing` block a grader copies into
`grading.json`, which hides `timing.json` from the benchmark's token count.

Generate the viewer with `python3 S review <iteration> …`, which runs skill-creator's
`eval-viewer/generate_review.py` with its arguments passed through — and with `</` escaped
in the data it inlines, since an HTML output such as a proposal page otherwise ends the
viewer's script and it renders empty. Add `--previous-workspace <iteration-(N-1)>` when an
earlier iteration exists.

- **With a browser** — run it as a server, `nohup python3 S review <iteration> --skill-name
  <target> --benchmark <iteration>/benchmark.json > <iteration>/viewer.log 2>&1 &`, and open
  http://localhost:3117 — in the Claude desktop app, in the Browser pane.
- **Without one** — add `--static <iteration>/review.html` and give the path.

Then **stop**. Tell the user what they are looking at — the Outputs tab, one run at a time
with its grades; the Benchmark tab, pass rates and cost per configuration — and that
"Submit All Reviews" writes `feedback.json`. Nothing else happens until the user has
reviewed: read `feedback.json` first (the server writes it into the iteration; the static
page downloads it — copy it in), and act on each comment. Kill the server when done.

## Trigger evals

**Which skills qualify:** only those the model can invoke by description — no
`disable-model-invocation: true`, and not a knowledge skill that is only ever preloaded by
an agent's `skills:` list. Typed skills are started by a person; their description is
documentation, not a trigger.

**The set** is `evals/sets/<target>.trigger.json`, committed, in skill-creator's format: a
JSON list of `{"query": "...", "should_trigger": true|false}`. Write the queries the way
skill-creator says to: realistic and specific, with paths, names and context, as a person
would type them; 8–10 that should trigger and 8–10 that should not, the negatives
near-misses — the same words or the same job in a place this skill does not own — rather
than obviously unrelated. `python3 S validate` checks the shape and the counts.

**The guard.** Every trigger set includes at least three should-not-trigger queries that are
the same task *outside* a plugin repo (the scoping clause this plugin's `CLAUDE.md` requires
in every description). A description from `run_loop` is applied only if (a) its held-out
score beats the current one, (b) every one of those scoping queries still does not trigger,
and (c) it still contains the current description's scoping clause — for a skill that has
it, the phrase `only inside a plugin's own subdirectory`. Otherwise the current description
stays, and the log says why.

**Where it runs.** `run_eval.py` tests a *description*, not the installed skill: it writes
it as a temporary command into `<project>/.claude/commands/`, where `<project>` is the
nearest ancestor of the working directory with a `.claude/`, and runs `claude -p` there.
So, every time:

1. A scratch project outside any repo (the session scratchpad), with its own `.claude/` —
   otherwise the command lands in `~/.claude/commands/`, and a repo's `CLAUDE.md` would
   tell the model it is in a plugin.
2. The plugin under test disabled there — `.claude/settings.json`
   `{"enabledPlugins": {"<plugin>@<marketplace>": false}}` — otherwise its real skill wins
   and scores as a miss.
3. `--num-workers 1` — parallel workers write identically described commands at once and
   the model picks a sibling's, which scores as a miss.
4. Run from the scratch project with `PYTHONPATH=<skill-creator>`, not from the
   skill-creator directory, whose nearest `.claude/` is `~`. `--skill-path` points at the
   skill in the plugin; nothing is copied.

```
cd <scratch> && PYTHONPATH=<sc> python3 -m scripts.run_eval --eval-set <set> --skill-path <skill dir> --num-workers 1 --runs-per-query 3 --model <session model> --verbose
cd <scratch> && PYTHONPATH=<sc> python3 -m scripts.run_loop --eval-set <set> --skill-path <skill dir> --num-workers 1 --model <session model> --max-iterations 5 --report none --results-dir <plugin>/evals/workspace/<target>/trigger --verbose
```

Optimize only when `run_eval`'s accuracy is below 0.9. `run_loop` is long — run it in the
background, one skill at a time, tailing its output for progress; it holds out 40% of the
set and reports the best description by held-out score, with iteration 1 the current
description. Apply its best only under the guard, editing `description:` and nothing else.

**Record.** The rate before, the rate after, and the applied description — before and after
text — or the reason none was applied go to `log-eval` as `**Trigger rate:**`.

## Blind comparison

Assertions answer "did it do the things"; they do not answer "is the new one better". When
both configurations pass everything, the pass rates are the same number and the change the
target just made is invisible to its own set. Blind comparison asks skill-creator's
comparator which output is better, without telling it which side is the working tree.

**When.** Only when the phase note's Evals row says `blind`, or the user asks for it. It is
not automatic: on a prose edit the two sides pass alike nearly every time, and a comparator
asked which of two near-identical outputs is better answers with noise — over nineteen
phases of one plan, 154 comparators returned tallies like 7/15 and 3/7
(`dev-team/evals/2026-10-10-determinism-phase9-behavioral.md`). It earns its cost where a
change is meant to make the output *better* in a way no expectation states. A
`without_skill` baseline does not need it — the assertions already separate the two.

**It reuses the iteration.** No new executor runs; the cost is one comparator per eval, over
the outputs `run-1` already produced — which needs both sides in the iteration, so not a
working-tree-only one with nothing reused.

```
python3 S blind <iteration-dir>
```

That stages each eval's two output directories as `eval-*/blind/A` and `eval-*/blind/B` in a
random order, writes which is which to `eval-*/blind/key.json`, and prints one entry per eval
with `eval`, `a_dir`, `b_dir`, `prompt`, `expected_output`, `expectations` and
`withheld_expectations`. The key is in neither what it prints nor any prompt below.

The comparator sees the two `outputs/` copies and no transcript, so `expectations` is the
eval's list without the ones that name the transcript, and `withheld_expectations` counts
those: handed over, each would fail for both sides and say nothing. The graders have already
checked them with the transcript in hand.

One comparator per eval, all in one message, each a general-purpose subagent:

> Read `<skill-creator>/agents/comparator.md` and follow it. output_a_path: `<a_dir>`.
> output_b_path: `<b_dir>`. eval_prompt: `<prompt>`. expectations: `<the entry's
> expectations as a JSON list>`. The output the task should have produced, for context:
> `<expected_output>`. Write your comparison to `<eval dir>/blind/comparison.json` in the
> shape that file defines. Read nothing else under the iteration directory — A and B are all
> you are given. You have no transcript: an expectation you cannot check from A and B alone
> is left out of your results, not failed for both.

Read `comparator.md` first: it owns its input names and the shape of `comparison.json`, and
if the file has moved on from this prompt, follow the file and record the difference as a
Deviation.

Then un-blind. Each `comparison.json` has a `winner` of `A`, `B` or `TIE`; `key.json` says
which configuration wore that label. Append the result to `<iteration>/benchmark.md`:

```markdown
## Blind comparison

| Eval | Winner | Configuration | Score A / B | Why |
|---|---|---|---|---|
```

— one row per eval, then the tally: how many of how many the working tree's version won, a
tie counting for neither. That tally is `**Blind:** new preferred k/n` in the log-eval entry.
A loss is reported as a loss: a comparator that prefers the baseline on a changed target is
the finding, not a number to bury.

## Without the runner

`S run` needs the `claude` CLI on `PATH` (or its path in `RUN_EVALS_CLAUDE`) and exits 2
without it. Its sessions run under the account that CLI is logged into, which is not
always the account of the chat that started it: `claude auth status` says which, and a run
that ends `not run` on a usage limit is that account's limit. It is also the wrong tool for
an eval that only means something inside a subagent: a hook keyed on `agent_type`, a tool
list a session's main thread does not have. Then the iteration is laid out with `S init …
--by-hand` — the mark plugin-dev's Agent guard looks for; without it the guard refuses an
executor or grader spawned through the Agent tool — and the same manifest is run by hand:

1. Spawn every run the manifest owes (`reused_from` null; read the manifest for this, it
   is this chat's input now) **in one message**, each a
   general-purpose subagent on the manifest's model, given the **Executor** block of
   `references/prompts.md` filled from its manifest entry (`<scratch>` is the session
   scratchpad, or a `mktemp -d` of your own) — at most 20 running at once (`plugin-anatomy`,
   `references/agents.md`); start the rest as slots free. As each finishes, `python3 S
   timing <run_dir> --tokens N --duration-ms N` from its completion notice — the only place
   those numbers exist. An executor ended by an error, or one that read what it is graded
   on, is rerun once by the same rule as the runner's; write `not-run.json` yourself on the
   second.
2. One grader per run that has no `grading.json`, the **Grader** block, all in one message,
   once every executor has finished. A grader prompt is never written anywhere an executor's
   rules let it read while one is still running; a staged prompt goes in the session
   scratchpad, outside the iteration.
3. `python3 S finalize <iteration>`, then `python3 S report <iteration>`, and continue from
   step 4 of the loop.

Each completion notice is a turn of this chat, so this costs what the runner exists to save:
use it for the evals that need it, not for a whole set.

## When skill-creator is missing

`python3 S locate-skill-creator` exits 1, and the manifest's `skill_creator` is null. Then:

- The grader is given its rules inline — the **Grader, no skill-creator** block of
  `references/prompts.md`, which `S run` picks on its own: PASS needs quoted evidence of
  genuine completion, not surface compliance; superficial or unverified is FAIL; the same
  `grading.json` shape.
- `S run`'s report is the benchmark: there is no `aggregate_benchmark`.
- There is no viewer: the report and the output paths go in chat for review, and the stop is
  the same.
- There is no blind comparison: it is `comparator.md` that defines the rubric and the
  verdict shape, and a comparator improvising both is not the same instrument twice.

The log says "graded inline — skill-creator not found".

## Record

Invoke `log-eval` with the set file, the eval IDs, the iteration directory, the baseline ref,
both pass rates (the baseline's marked *reused* when no baseline ran in this iteration, or
*not run* for a working-tree-only iteration with none), the model the executors, graders and
comparators ran on, the report's Cost lines, and any run recorded as not run, before
reporting results anywhere else. The log is written from the report: its table, its failed
expectations and what was concluded about each. `evals/workspace/` is never
committed; the set and the log are.
