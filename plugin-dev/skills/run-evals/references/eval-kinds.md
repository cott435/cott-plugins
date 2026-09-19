# Eval kinds

The one list of the kinds of eval plugin-dev runs. `run-evals` names no kind this file does
not define, and a phase note's Evals table uses these names in its Kind column.

## The kinds

1. **mechanical** — a script or `check-contracts`; no model. Pass/fail is the exit code.
   Examples: a file exists, frontmatter parses, `eval_workspace.py validate` exits 0, a
   planted defect makes a check fail. Runs first; a failing mechanical check stops the run,
   because a broken bundle makes every later result meaningless.
2. **load** — the plugin loads from its working copy and the new pieces register. One
   `claude -p` call: `claude --plugin-dir <plugin> -p "List the skills and agents you have
   from <plugin>"`. Pass when every new name appears in the answer.
3. **behavioral** — the loop in `SKILL.md` **The behavioral loop**: the target and its
   baseline run the set's prompts side by side, a grader checks each expectation against
   the outputs with quoted evidence, then the benchmark and the viewer. The pass bar comes
   from the phase note; the default is every expectation passing for `with_skill`, and its
   pass rate at least the baseline's.
4. **trigger** — Phase 2 adds this kind.
5. **platform-fact** — a fact about Claude Code or a tool that the docs do not settle. Run
   once, in phase 0 of a plan (or first thing in phase 1), with the assumed answer written
   down before the test. No later phase may depend on it until its result is logged.

## Baselines

What a behavioral eval's baseline configuration runs, from the set's `baseline` field:

- `none` — a new target with no prior version. The baseline is `without_skill`: the same
  prompt done with no target file at all.
- `previous` — the target as of the commit the current work started from: the merge-base
  with the default branch when HEAD is on another branch, otherwise HEAD itself (the parent
  of uncommitted work). The baseline is `old_skill`.
- a git ref (a tag, a SHA) — the target as of that ref, also `old_skill`.

The snapshot is the target's whole directory (`git archive`), so its `references/` and
`scripts/` come with it.

An agent is run by giving a general-purpose subagent its prompt file as instructions. Its
`tools:` list and `skills:` preloads are not reproduced, so a behavioral result about what
the agent does with its tools says "proxy" in the log.

## Harness rules

Every executor, with-target or baseline, runs under these; they override the target where
they conflict:

- **No live user.** Wherever the target would ask, the executor writes the question and its
  options to `outputs/interview.md`, then answers from the eval's harness file — or with the
  option marked Recommended when the harness does not cover the question — and continues.
- **No side effects in the repo.** No publishing, committing, pushing, branching, or writing
  anywhere in the repo. Whatever it would publish or write goes into its `outputs/`.
- **It keeps its own transcript.** `transcript.md` in the run directory: each step, what it
  read, what it decided, and its final message to the user. A subagent cannot export its
  real transcript, and the grader needs one.
- **It stops at the target's first approval point**, or when the task is done.

## Cost

| Kind | Cost |
|---|---|
| mechanical | seconds; no model |
| load | one `claude -p` call, ~10k tokens |
| behavioral | prompts × 2 executors plus one grader per run — ~0.8M tokens for 3 prompts cold, ~0.4M warm |
| trigger | phase 2 |
| platform-fact | one small test each, usually under 50k tokens |
