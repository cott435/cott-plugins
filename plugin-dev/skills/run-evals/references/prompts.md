# The prompts a run sends

The one copy of the executor and grader prompts. `eval_workspace.py run` reads the fenced
block under each heading below, fills every `<…>` from the run's manifest entry, and passes
the result to a headless session; a run spawned by hand through the Agent tool (`SKILL.md`,
**Without the runner**) is given the same block, filled the same way. A heading renamed here
is renamed in `eval_workspace.py`'s `PROMPT_HEADINGS`.

What each rule is for is in `eval-kinds.md`, **Harness rules**.

## Executor

For `with_skill` and `old_skill`. `<target_file>` and `<plugin_root>` are the run's own
manifest values: the working tree's for `with_skill`, the copies under `baseline-snapshot/`
for `old_skill`, so the baseline runs the old version of every file of the plugin it reads,
not only of the target. `<harness>` is the eval's harness file, or the words *no harness
file* when it has none. `<scratch>` is a directory the runner made for this run alone.

```text
You are testing `<target>` by executing it. Your first tool call is the Read tool on
`<target_file>`; no other command comes before it, and you read every file with Read.
Follow that file as if the user had typed: `<prompt>`. The repo is `<repo root>`.
Your plugin root is `<plugin_root>`. Wherever the target says `${CLAUDE_PLUGIN_ROOT}`, or
names another file of its plugin — a skill, an agent, a script, a template — use the copy
under that directory and no other copy.
Harness rules — these override the target where they conflict:
- There is no live user. Wherever the target would ask, write the question and its
  options to `outputs/interview.md`, then answer from `<harness>` (or the option marked
  Recommended when it does not cover the question) and continue.
- Do not publish, commit, push, create branches, or write anywhere in the repo. Write
  whatever you would publish or write into `<outputs_dir>` instead.
- Read nothing under `<iteration>` except your own run directory `<run_dir>` — and
  `baseline-snapshot/` when your plugin root is inside it — and nothing under
  `<plugin dir>/evals/sets/` except what this prompt or the harness file names. What your
  run is graded on is kept in both, and a run that reads it is thrown away.
- Any copy of a repo or fixture you work on goes in a directory you create yourself with
  `mktemp -d <scratch>/eval.XXXXXX`, never at a path another run could share. Delete
  nothing you did not create.
- Keep `<run_dir>/transcript.md`: each step, what you read, what you decided, and your
  final message to the user.
- Stop at the target's first approval point, or when the task is done.
Reply with a two-line summary.
```

## Executor, no target

For a `without_skill` baseline: no target file and no plugin root are named. The harness
rules are the same.

```text
Do the following task as you would without any special instructions: `<prompt>`
The repo is `<repo root>`.
Harness rules:
- There is no live user. Wherever you would ask, write the question and its options to
  `outputs/interview.md`, then answer from `<harness>` (or the option marked Recommended
  when it does not cover the question) and continue.
- Do not publish, commit, push, create branches, or write anywhere in the repo. Write
  whatever you would publish or write into `<outputs_dir>` instead.
- Read nothing under `<iteration>` except your own run directory `<run_dir>`, and nothing
  under `<plugin dir>/evals/sets/` except what this prompt or the harness file names. What
  your run is graded on is kept in both, and a run that reads it is thrown away.
- Any copy of a repo or fixture you work on goes in a directory you create yourself with
  `mktemp -d <scratch>/eval.XXXXXX`, never at a path another run could share. Delete
  nothing you did not create.
- Keep `<run_dir>/transcript.md`: each step, what you read, what you decided, and your
  final message to the user.
- Stop at the first point you would ask for approval, or when the task is done.
Reply with a two-line summary.
```

## Grader

One per run, once every executor has finished. `<expectations>` is the eval's expectations
as a JSON list.

```text
Read `<skill-creator>/agents/grader.md` and follow it. expectations: <expectations>.
transcript_path: `<run_dir>/transcript.md`. outputs_dir: `<run_dir>/outputs`. Write
`<run_dir>/grading.json` with an `expectations` array whose items have exactly the fields
`text`, `passed`, `evidence`, and a `summary` with `passed`, `failed`, `total`, `pass_rate`.
Quote evidence; a claim in the transcript that the outputs do not bear out is a FAIL. Reply
with one line: the pass count.
```

## Grader, no skill-creator

The same grader with its rules inline, for a machine where `locate-skill-creator` finds
nothing.

```text
Grade one run of an eval. expectations: <expectations>. transcript_path:
`<run_dir>/transcript.md`. outputs_dir: `<run_dir>/outputs`. Read the transcript and every
file under the outputs directory. For each expectation decide PASS or FAIL: PASS needs
quoted evidence of genuine completion, not surface compliance; superficial, unverified, or
claimed in the transcript and not borne out by the outputs is FAIL. Write
`<run_dir>/grading.json` with an `expectations` array whose items have exactly the fields
`text`, `passed`, `evidence`, a `summary` with `passed`, `failed`, `total`, `pass_rate`,
and an `eval_feedback` object whose `suggestions` list names any expectation that is
trivially satisfied or any outcome nothing checks (`assertion`, `reason`). Reply with one
line: the pass count.
```
