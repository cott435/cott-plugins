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
3. **trigger** — for a skill the model invokes by its description: skill-creator's
   `run_eval.py` runs each query of `evals/sets/<target>.trigger.json` three times through
   `claude -p` and scores whether the description was picked, should-trigger and
   should-not alike. Below 0.9, `run_loop.py` proposes better descriptions, applied only
   under the guard in `SKILL.md` **Trigger evals**, which also says where it must run.
4. **behavioral** — the loop in `SKILL.md` **The behavioral loop**: the target runs the
   set's prompts, a grader checks each expectation against the outputs with quoted evidence,
   and one report comes back. Compared, the baseline runs the same prompts beside it, once
   per ref — a later iteration reuses that run. Working tree only, no baseline runs at all:
   a regression check (**When regression runs**, below). The pass bar comes from the phase
   note; the default is every expectation passing for `with_skill`, and, where there is a
   baseline, its pass rate at least the baseline's.
5. **platform-fact** — a fact about Claude Code or a tool that the docs do not settle. Run
   once, in phase 0 of a plan (or first thing in phase 1), with the assumed answer written
   down before the test. No later phase may depend on it until its result is logged.

## Baselines

What a behavioral eval's baseline configuration runs, from the set's `baseline` field:

- `none` — a new target with no prior version. The baseline is `without_skill`: the same
  prompt done with no target file at all.
- `previous` — the plugin as of the commit the current work started from: the merge-base
  with the default branch when HEAD is on another branch, otherwise HEAD itself (the parent
  of uncommitted work). The baseline is `old_skill`.
- a git ref (a tag, a SHA) — the plugin as of that ref, also `old_skill`.

The default branch is `origin/HEAD` when the clone has one, else the first of `main`,
`master`, `origin/main`, `origin/master` that exists — a clone made for one branch often has
only the remote-tracking one. When none exists, or HEAD has no merge-base with it,
`previous` falls back to HEAD and `eval_workspace.py init` says so in a warning: with the
work already committed, HEAD is the version under test.

The snapshot is the **whole plugin directory** at that ref (`git archive`), minus `evals/`,
under `baseline-snapshot/` in the iteration. A target reads its plugin's other files — a
skill it invokes, a script, a template — through `${CLAUDE_PLUGIN_ROOT}`, so the baseline
executor is told the snapshot is its plugin root, and reads the old version of all of them.
A snapshot of the target's directory alone left the baseline reading every other file from
the working tree: a change to a skill the target reads then showed up on both sides
(`dev-team/evals/2026-09-30-2.2-architect-skills.md`). `evals/` is left out because it holds
the sets, and so the expectations. The snapshot keeps its `.claude-plugin/plugin.json`, so
a headless baseline can load it with `claude --plugin-dir`.

The snapshot is made only when a baseline executor will run in this iteration. A baseline
run an earlier iteration of the same target finished — same ref, same model, same
`inputs_hash` (the prompt, the harness sheet and every path under the eval's `files`) — is
copied in instead and marked `reused_from` in the manifest: the plugin at a ref does not
change, so neither does what a run of it is given. Its grades are reused with it unless the
eval's expectations changed, in which case it is graded again. A manifest written before
`inputs_hash` existed is passed over; `init --reuse-unhashed` accepts it on the prompt and
the harness file's name, which is right only if no seed or harness sheet changed since.

A phase note's **Baseline** cell may also say `working tree only`, which is not a baseline
but the instruction to run none: `init --working-tree-only`. The set's own `baseline` field
still names the ref, for the reuse above and for the one compared rerun a failed expectation
gets.

`init` also warns when the plugin at the baseline ref is identical to the working tree
(outside `evals/`): the two configurations would run the same files. Both warnings are in the
manifest's `warnings` and on stderr, and neither stops `init` — the baseline may be right,
as when the files under test are a fixture's rather than the plugin's.

An agent is run by giving a headless session its prompt file as instructions. Its `tools:`
list and `skills:` preloads are not reproduced, so a behavioral result about what the agent
does with its tools says "proxy" in the log. An eval that only means something inside a
subagent — a hook keyed on `agent_type` — is run through the Agent tool instead (`SKILL.md`,
**Without the runner**).

## When behavioral evals run

A behavioral eval is run for one of two reasons: to prove a change (it is new, and the
baseline is expected to fail it) or as regression (it passed before; does it still). Either
way it tests a file as it is when it runs, so a run made before a later phase edits that
file again tests a version nobody ships. In one 37-phase plan one agent's file was edited by
10 of the first 19 phases and its evals rerun after most of them; a prose-only phase reran
15 evals on both sides for 126/136 against 123/136
(`dev-team/evals/2026-10-10-determinism-phase9-behavioral.md`). So:

- **Every phase runs its mechanical rows**, all of them: they cost nothing.
- **A target's behavioral evals run once, after its last edit**: at the first checkpoint at
  or after the last phase that touches the target or anything it is made of — its own file
  or directory, the skills an agent preloads, the paths its set lists under `depends_on`.
  New evals and existing ones alike. `scripts/phases.py touch` prints that phase per target
  from an edit list.
- **A checkpoint** is a phase the plan names (`**Checkpoints:**` in the overview) where
  targets that are finished get their evals. The last phase is always one. Add an earlier
  one where targets finish early, so their result does not wait for the end.
- **New evals run compared**, the one time they run, since their point is that the baseline
  fails them. **Existing evals run working tree only.**
- **A regression found at a checkpoint** is a failed expectation the baseline passes. The
  commits since the plan's branch point that touched the target are the suspects
  (`git log --oneline <branch point>..HEAD -- <target_path>`), and the fix is the checkpoint
  phase's own.
- **Outside a plan**, a change to one target runs that target's evals once, when the change
  is done: the new ones compared, the rest working tree only.

## Per component

What a mechanical or load row checks depends on the component it is about. Each of
`plugin-anatomy`'s component references (`skills.md`, `agents.md`, `hooks.md`, `mcp.md`,
`manifest.md`) ends with a **How to test it** table: the checks for that kind, and which kind
of eval each is. A phase that adds a hook or an MCP server takes its load row from there, since
`claude -p` listing skills and agents shows neither.

A `platform-fact` result is written back to `plugin-anatomy` (the fact's status becomes
`[proven: <log>]`, or the fact is corrected), so the next design finds it settled.

## Harness rules

Every executor, with-target or baseline, runs under these; they override the target where
they conflict:

- **No live user.** Wherever the target would ask, the executor writes the question and its
  options to `outputs/interview.md`, then answers from the eval's harness file — or with the
  option marked Recommended when the harness does not cover the question — and continues.
- **No side effects in the repo.** No publishing, committing, pushing, branching, or writing
  anywhere in the repo. Whatever it would publish or write goes into its `outputs/`.
- **It reads the target first.** Its first tool call is a Read of the target file, with no
  other command before it. Without the line, executors explored the repo before reading
  their rules (`dev-team/evals/2026-09-29-2.2-designer-tester.md`).
- **One plugin root.** The working tree's plugin directory for `with_skill`, the snapshot's
  for `old_skill`. Every `${CLAUDE_PLUGIN_ROOT}` path and every other plugin file the target
  names is read under it and from no other copy.
- **It cannot see what it is graded on.** It reads nothing under the iteration directory
  outside its own run directory (and the snapshot, when that is its plugin root), and
  nothing under `evals/sets/` that its prompt or harness file does not name.
  `manifest.json`, `eval_metadata.json` at the eval and the configuration level, and the
  set itself all hold the expectations; a baseline executor once read the copy one level
  above its run directory (`dev-team/site/notes/2.2-progress.md`, phase 8). A run
  that read them is void and rerun: the runner checks every tool call of the session for
  those paths. A grader's prompt is passed to its session and never written to disk, and no
  grader starts before the last executor has finished.
- **Its scratch is its own.** A copy of a repo or fixture lives in a directory the executor
  makes with `mktemp -d` inside the scratch directory the runner made for that run alone,
  and it deletes nothing it did not create. Two parallel runs shared
  one copy in the session scratchpad and one ran `rm -rf` on it
  (`dev-team/evals/2026-09-30-2.2-implementer.md`).
- **It keeps its own transcript.** `transcript.md` in the run directory: each step, what it
  read, what it decided, and its final message to the user. A subagent cannot export its
  real transcript, and the grader needs one.
- **It stops at the target's first approval point**, or when the task is done.

An executor ended by an API error is rerun once; `SKILL.md` **The behavioral loop** step 3 has
the rule. Executors, graders and comparators run on the model `SKILL.md` **The model** names.
The prompts that carry these rules are `prompts.md`, the one copy.

## Cost

Tokens here count every turn's input, cache reads included, which is what a usage limit
counts; a run's final context size is some tenth of it. Measured on Sonnet 5.5 over 1,100
sessions of one plan (`dev-team/evals/`, the determinism logs of 2026-10-09 and -10):

| Kind | Cost |
|---|---|
| mechanical | seconds; no model |
| load | one `claude -p` call, ~10k tokens |
| trigger | 20 queries × 3 runs = 60 short `claude -p` calls, one at a time — ~20 min per skill; `run_loop` up to 5× that plus one rewrite call per iteration |
| behavioral, compared | per eval: two executors (~1.6M each; one that spawns its own agents, several times that) and two graders (~0.5M each) — ~4M the first time, ~2M once its baseline is reused |
| behavioral, working tree only | per eval: one executor and one grader — ~2M |
| blind comparison | one comparator per eval, ~0.4M |
| platform-fact | one small test each, usually under 50k tokens |

What a plan's split shows per phase is these, times the evals in its rows. The chat that
drives a run adds its own turns on top, each one a re-read of its whole context: with the
runner that is a handful per target; spawning the same runs through the Agent tool is one
turn per session, which on that plan cost as much again as every executor and grader
together.
