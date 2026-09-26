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
`added_in` saying which change added it — so the next change to the same target can rerun
it as a regression check. A test run only in a chat is a test nobody can repeat.

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

- `baseline` is `none` (a new target — the baseline runs without it), `previous` (the target
  as of the commit the current work started from: `git merge-base HEAD <default branch>`
  when on another branch, otherwise HEAD, the parent of uncommitted work), or an explicit git
  ref.
- `harness` is optional, and required for a target that asks the user anything: a file of
  scripted answers the executor uses in place of the user.
- Every expectation is observable in `outputs/` or `transcript.md` — a file exists, contains
  a thing, a count is under a limit, the chat message does or does not do something. "Is
  good quality" is not an expectation.
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
├── baseline-snapshot/                   git archive of the target's directory at the baseline ref
├── eval-<id>-<name>/
│   ├── eval_metadata.json               {eval_id, eval_name, prompt, assertions}
│   ├── with_skill/
│   │   ├── eval_metadata.json           same file again — the viewer reads it here
│   │   └── run-1/{outputs/, transcript.md, grading.json, timing.json}
│   └── old_skill/ | without_skill/      same shape
├── benchmark.json, benchmark.md         aggregate_benchmark.py
└── feedback.json                        the viewer, after review
```

`with_skill` is the target as it is in the working tree. The baseline is `old_skill` (a
snapshot at a ref) or `without_skill` (`baseline: none`). These are skill-creator's names;
agents use them too, since its benchmark labels configurations by them. Iterations are kept:
the next one is compared against the last.

## The behavioral loop

1. `python3 S validate evals/sets/<target>.json`
2. `python3 S init . <target> [--evals 1,2,3] [--baseline REF]` — prints a JSON manifest
   (also saved as `manifest.json` in the iteration): the iteration path, the baseline ref,
   the skill-creator directory or null, and one entry per run with `run_dir`,
   `outputs_dir`, `prompt`, `harness`, `target_file` and `expectations`.
3. Spawn every run in the manifest **in one message**, with-target and baseline together,
   each a general-purpose subagent given the executor prompt below. As each finishes,
   `python3 S timing <run_dir> --tokens N --duration-ms N` from its completion notice —
   the only place those numbers exist.
4. One grader per run, prompt below, all in one message.
5. `python3 S finalize <iteration-dir>` — the grader copies `timing` into `grading.json`,
   which hides `timing.json` from the benchmark's token count; this drops the copy. Then,
   from the skill-creator directory: `python3 -m scripts.aggregate_benchmark
   <iteration-dir> --skill-name <target>`. A 0% row means check the tree before believing
   it. Its Delta column is the first configuration alphabetically minus the second, so
   against `old_skill` the sign is inverted — read the two rows, not the delta.
6. The viewer (see **Review**).
7. Read each grader's critique of the expectations themselves: an expectation it calls
   trivially satisfied, or an outcome it says nothing checks, is rewritten or added in the
   set, in this change.

The executor prompt, verbatim with `<…>` filled:

> You are testing `<target>` by executing it. Read `<target file, or the snapshot's copy
> for the baseline>` and follow it as if the user had typed: `<prompt>`. The repo is
> `<repo root>`.
> Harness rules — these override the target where they conflict:
> - There is no live user. Wherever the target would ask, write the question and its
>   options to `outputs/interview.md`, then answer from `<harness>` (or the option marked
>   Recommended when it does not cover the question) and continue.
> - Do not publish, commit, push, create branches, or write anywhere in the repo. Write
>   whatever you would publish or write into `<outputs_dir>` instead.
> - Keep `<run_dir>/transcript.md`: each step, what you read, what you decided, and your
>   final message to the user.
> - Stop at the target's first approval point, or when the task is done.
> Reply with a two-line summary.

For a `without_skill` baseline the first sentence becomes "Do the following task as you
would without any special instructions:" and no target file is named.

The grader prompt, verbatim with `<…>` filled:

> Read `<skill-creator>/agents/grader.md` and follow it. expectations: `<the eval's
> expectations as a JSON list>`. transcript_path: `<run_dir>/transcript.md`. outputs_dir:
> `<run_dir>/outputs`. Write `<run_dir>/grading.json` with an `expectations` array whose
> items have exactly the fields `text`, `passed`, `evidence`, and a `summary` with
> `passed`, `failed`, `total`, `pass_rate`. Quote evidence; a claim in the transcript that
> the outputs do not bear out is a FAIL.

## Review

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

**When.** For a changed target (an `old_skill` baseline), after grading: automatically when
every expectation passed in both configurations, or when the two pass rates are within 10
points; otherwise only when the phase note's Evals row says `blind`. A `without_skill`
baseline does not need it — the assertions already separate the two.

**It reuses the iteration.** No new executor runs; the cost is one comparator per eval, over
the outputs `run-1` already produced.

```
python3 S blind <iteration-dir>
```

That stages each eval's two output directories as `eval-*/blind/A` and `eval-*/blind/B` in a
random order, writes which is which to `eval-*/blind/key.json`, and prints one entry per eval
with `eval`, `a_dir`, `b_dir`, `prompt`, `expected_output` and `expectations`. The key is in
neither what it prints nor any prompt below.

One comparator per eval, all in one message, each a general-purpose subagent:

> Read `<skill-creator>/agents/comparator.md` and follow it. output_a_path: `<a_dir>`.
> output_b_path: `<b_dir>`. eval_prompt: `<prompt>`. expectations: `<the eval's expectations
> as a JSON list>`. The output the task should have produced, for context:
> `<expected_output>`. Write your comparison to `<eval dir>/blind/comparison.json` in the
> shape that file defines. Read nothing else under the iteration directory — A and B are all
> you are given.

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

## When skill-creator is missing

`python3 S locate-skill-creator` exits 1, and the manifest's `skill_creator` is null. Then:

- The grader is a general-purpose subagent given the grading rules inline: PASS needs quoted
  evidence of genuine completion, not surface compliance; superficial or unverified is FAIL;
  write `grading.json` in the same shape.
- Pass rates are computed by hand into `<iteration>/benchmark.md`, one row per
  configuration.
- There is no viewer: the per-expectation table and the output paths go in chat for review,
  and the stop is the same.
- There is no blind comparison: it is `comparator.md` that defines the rubric and the
  verdict shape, and a comparator improvising both is not the same instrument twice.

The log says "graded inline — skill-creator not found".

## Record

Invoke `log-eval` with the set file, the eval IDs, the iteration directory, the baseline ref
and both pass rates, before reporting results anywhere else. `evals/workspace/` is never
committed; the set and the log are.
