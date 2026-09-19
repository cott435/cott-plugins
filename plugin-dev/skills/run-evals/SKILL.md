---
name: run-evals
description: Run the evals for one skill or agent of a Claude Code plugin - mechanical checks, a load check, behavioral runs against a baseline graded assertion by assertion with skill-creator's grader, benchmark and viewer, and trigger tests for skills the model invokes - then record the result with log-eval. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), whenever a phase note or a change calls for evals, or before claiming that a skill or agent behaves a certain way.
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

Within one run the order is mechanical, then load, then behavioral, then trigger. A failing
mechanical check stops the run: a bundle that does not pass its own checks makes behavioral
results meaningless, so fix it first. `platform-fact` evals are not part of a target's run;
a plan runs them once, before anything depends on them.

## The set

`evals/sets/<target>.json`, committed. The shape:

```json
{
  "target": "plan-phases",
  "target_path": "skills/plan-phases/SKILL.md",
  "evals": [
    {
      "id": 1,
      "name": "trading-research-three-jobs",
      "kind": "behavioral",
      "baseline": "previous",
      "harness": "evals/sets/files/plan-phases/trading.md",
      "prompt": "/plugin-dev:plan-phases --new trading-agents a plugin for stock research agents",
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
problem as `path: eval <id>: <problem>`.

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

## When skill-creator is missing

`python3 S locate-skill-creator` exits 1, and the manifest's `skill_creator` is null. Then:

- The grader is a general-purpose subagent given the grading rules inline: PASS needs quoted
  evidence of genuine completion, not surface compliance; superficial or unverified is FAIL;
  write `grading.json` in the same shape.
- Pass rates are computed by hand into `<iteration>/benchmark.md`, one row per
  configuration.
- There is no viewer: the per-expectation table and the output paths go in chat for review,
  and the stop is the same.

The log says "graded inline — skill-creator not found".

## Record

Invoke `log-eval` with the set file, the eval IDs, the iteration directory, the baseline ref
and both pass rates, before reporting results anywhere else. `evals/workspace/` is never
committed; the set and the log are.
