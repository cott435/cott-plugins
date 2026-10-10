---
name: run-phase
description: Do the next unfinished phase of a plan written by plan-phases - a change to a plugin, a new plugin being built up, or a reviewed plugin's edit list - read the spec, the overview and the progress ledger, write that phase's note from its scope and the files as they are now (or read the note when the plan already has one), make exactly its edits, run the plugin's checks and the phase's evals, log them, commit once, update the ledger, and stop. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), one phase per Claude Code chat, typed by the user.
argument-hint: "[slug]"
disable-model-invocation: true
---

# Running one phase

A phase is one chat's worth of work. `plan-phases` fixed what it owns, what it may not
touch and how it is proved, in the overview; this chat turns that into a note against the
files as they are now, does what the note says, proves it with the overview's evals for the
phase, commits once, records where things stand, and stops. The next chat starts from the
ledger, not from a summary of this one.

The note is written here rather than at planning time because a note names exact lines, and
the earlier phases of a plan move them. A plan written before notes moved here already has
every note; then this chat reads its note instead of writing one.

`E` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/edits.py`.

## Find the work

1. Confirm this is a plugin subdirectory (`.claude-plugin/plugin.json` exists).
2. Locate the ledger: `site/notes/<slug>/<slug>-progress.md`. With no slug argument and exactly one
   ledger, use it; with several, ask which. With none, stop — `plan-phases` has not run.
3. Confirm the branch: `git branch --show-current` equals the branch the ledger names. If
   not, stop and say so; never switch branches on the user's behalf.
4. Confirm a clean tree: `git status --porcelain` is empty, or every listed path is one the
   ledger's `in progress` row names under Notes. Anything else stops with the list.
5. Resolve SHAs: for every `done` row whose Commit cell is a `(phase N)` prefix, replace it
   with `git log --format=%h --grep='(phase N)'`. This edit rides in this chat's commit.

## Read, in this order, and nothing else up front

1. The spec, for the why:
   - `site/notes/<slug>/<slug>-design.md` when there is one: the workflows and their charts,
     the decisions, the non-goals, as approved. Plans written before `design-plugin` existed
     have none; their overview carries it.
   - `site/notes/<slug>/<slug>-edits.md` when there is one, never whole: its **Goal**,
     **Decisions taken** and **What must not break** sections
     (`sed -n '/^## <name>/,/^## /p'`).
2. `site/notes/<slug>/<slug>-00-overview.md` — what the spec turns into: the contents tree,
   the files other files parse, the phases table, the eval rows by phase, the breaking
   changes.
3. `site/notes/<slug>/<slug>-progress.md` — the first row whose status is not `done` is this
   chat's phase. `in progress` means a previous chat stopped mid-way: read its Notes cell
   and `git status`, and finish rather than restart. Phase 0 is the exception: `plan-phases`
   leaves it `in progress` on purpose when it has platform-fact evals, listed in its Notes
   cell. Running those evals is this chat's phase; the overview is its note.
4. That phase's note, `site/notes/<slug>/<slug>-NN-<name>.md`, if it exists. If it does not,
   this phase's items, when the spec is an edit list:
   `E show site/notes/<slug>/<slug>-edits.md --phase <N> --overview site/notes/<slug>/<slug>-00-overview.md`,
   which prints the items the overview gives this phase and the decisions they cite. Then
   write the note, per **Write the note**.

Open plugin files as the note's steps reach them. Do not read other phases' notes or items,
the evals of other phases, findings files, or any earlier conversation: the spec and the
overview carry what they concluded, and another phase's work is not this chat's job. A
phase never edits the spec or the overview: where the note cannot follow them, the
disagreement is a Deviation.

## Write the note

Only when the phase has no note yet. The note is the plan for this chat's edits, written
before any of them, and it rides in the phase's commit, so the next reader sees what was
planned beside what was done.

Write it from `${CLAUDE_PLUGIN_ROOT}/templates/phases/phase.md`, at
`site/notes/<slug>/<slug>-NN-<name>.md` with the name the overview's Phases row gives. Its
sections, in order:

- **`# NN — <name>`**, then a purpose paragraph: what the phase adds and the gap it closes,
  from the overview's row and the spec.
- **`## Decisions`**: anything settled here rather than in the spec, each with its reason:
  a name, a placement, the order of two edits. A decision that is the user's (a default
  that changes behavior, a choice between two designs the spec did not take) is not
  settled here: stop and ask it, with the recommended option first, and write the answer
  here.
- **`## Files`**: a Path · Change table, one row per file, naming the section each edit
  lands in: the files the phase's items or components name, plus what the plugin's own
  rules require for an added or removed file. Nothing the overview says this phase must
  not touch.
- **`## Specification`**: the exact content. Frontmatter, heading names, rules,
  `contracts.yml` entries, and any prompt another model will be given, verbatim. Frontmatter
  uses only the keys in the component's `plugin-anatomy` reference, and the note names that
  reference beside each new component. Every name in the overview's **Files other files
  parse** is used exactly as the overview gives it.
- **`## Steps`**: ordered so the bundle is consistent after each one.
- **`## Evals`**: this phase's rows from the overview's **Evals by phase**, copied, columns
  `| ID | Kind | Target | Baseline | Set evals | Pass bar |`. A pass bar is never loosened
  here.
- **`## Done when`**: conditions checkable without judgment.

Against an edit list, each item's lines are where the review found them, and earlier phases
have moved them since. For every `path:line` an item cites, find the quoted text in the file
as it is now (`grep -nF`), and cite the line where it is. When the text is gone because an
earlier phase already made the change, say so under Decisions and drop that edit; when it is
gone for any other reason, the item cannot be followed as written, which is a Deviation.

`references/example-phase.md` walks through a real note.

## Do the phase

Follow the note's **Steps** in order. Whatever the note says, these always apply:

- **Only this phase's edits.** A thing that would be nice to fix but is not in the note is
  a line under this phase's Notes cell in the ledger (*noticed: …*), not an edit. One
  exception: the eval sets this phase's own `run-evals` run reads. When its graders'
  critique of the expectations names one as trivially satisfied, vacuous, or checking an
  outcome the outputs cannot show, correcting it in `evals/sets/<target>.json` is part of
  this phase — `run-evals`' own step 7 requires it, and a set nobody is allowed to fix is a
  set that rots. Correct the expectation, say so in the eval log, and rerun only if the
  rewrite changes a verdict. This covers the expectations, not the target's behavior: a
  change to what the phase *builds* is still out of scope.
- **Read the component's reference first.** Before creating or changing an agent, skill,
  hook, MCP server or manifest field, read its file in
  `${CLAUDE_PLUGIN_ROOT}/skills/plugin-anatomy/references/`. Where the note's frontmatter uses
  a key that reference does not document, or one plugins ignore, that is a Deviation, not a
  silent fix.
- **Write proven facts back.** A `platform-fact` row's result goes into `plugin-anatomy`: the
  fact's status becomes `[proven: <log>]`, or the fact is corrected and cites the log. When
  the plan is for plugin-dev itself, that edit is part of this phase. For any other plugin it
  is a different plugin's file, so it is a *noticed: write back to plugin-anatomy* line in the
  ledger, done afterwards as a small change to plugin-dev.
- **The plugin's own rules.** Its `CLAUDE.md` — a three-file rule, a naming list, a site
  order file — applies to every file the phase adds or removes, in the same commit.
- **Checks before evals.** If the plugin has `contracts.yml`, `check-contracts` passes. If
  it has `site/`, `build-site` runs. Both before the evals, so a failed contract is fixed in
  the file rather than discovered by an eval.
- **Evals, through `run-evals`.** For each target in the note's `## Evals` table, invoke
  `run-evals` with that target's rows — the set file, the eval IDs, the baseline — in the
  table's order (platform facts and mechanical rows first). A row whose Baseline cell says
  `working tree only` is a checkpoint's regression row and runs that way. Every result is
  logged with `log-eval` before it is reported here, a clean pass exactly like a failure,
  with the commit field reading *uncommitted — see working-tree diff*, since the phase's
  commit comes after.
- **The evals cost this chat a few turns, not one per run.** A phase's cost is its turns
  times its context, and the evals are where both grow. So: `init` every target's
  iteration first, start every `eval_workspace.py run` as a background command in one
  message, and do nothing until they exit — no polling, no reading `run.log`. Then read
  each iteration's report and nothing else of it; open one run's `transcript.md` or
  `outputs/` only for a failed expectation the report's evidence does not settle. Never
  spawn executors or graders through the Agent tool unless `run-evals`' **Without the
  runner** says this eval needs it. No blind comparison unless a row's pass bar says
  `blind`.
- **A regression found at a checkpoint is this phase's to fix.** A checkpoint row's failed
  expectation that the baseline passes was broken by an earlier phase. Find it —
  `git log --oneline <previous checkpoint's commit>..HEAD -- <target_path>`, then the diff
  of the commit the evidence points at — and fix it in that file, in this phase's commit:
  the one exception to *Only this phase's edits*, with the commit it corrects named under
  `## Deviations`. A failed expectation the baseline fails too, or one the report's
  evidence shows to be stale or a harness artifact, is not a regression: it is a line in
  the eval log and, when the expectation is at fault, a correction to the set.
- **Stop for review.** When any row is behavioral, stop once the viewer is open (or the
  results table is in chat, if skill-creator is missing) and wait for the user. Read
  `feedback.json` before continuing. Nothing is committed before the user has replied.
  Feedback asking for a change within the note's Files — or within the eval sets this
  phase ran, per the exception above — is part of this phase; anything else is a
  *noticed:* line in the ledger.
- **One fix, then a Deviation.** A missed pass bar: one fix inside the note's Files, rerun
  the evals that missed — those ids, not the whole row; their baselines are reused — as the
  next iteration, review again. Still missed: append the outcome
  — the bar, the result, what was tried — to `## Deviations` and ask whether to commit.
- **Notes written before 0.9** have no `## Evals` section; run the evals their Steps list
  names, as that list describes, and write "old-format note" in the ledger's Notes cell.
- **Deviations are written down.** Where the note could not be followed as written — a
  heading did not exist, a platform fact came out differently, a step was wrong — append a
  `## Deviations` section to the note (what the note said, what was done, why) and, if a
  later phase's assumption is now false (a heading in the overview's **Files other files
  parse** came out differently, an item a later phase owns was already made), one line in
  the ledger's Notes cell for that later phase. Never silently do something other than the
  note.
- **One commit.** All of the phase's edits, the eval logs, the note (written here, or its
  Deviations section), and the ledger row, staged by explicit path. Message from the note, in the form
  `<plugin> <slug> (phase N): <what>`. Nothing is pushed.
- **Never bump, never tag.** If the note says to propose a release — a bump at some level
  for a change, or tagging `0.1.0` as scaffolded for a new plugin — say so in chat with what
  the note names and stop; `bump-version` runs only on the user's yes.
- **A new plugin's phases build a bundle that must load.** After a phase that adds an agent
  or skill, `/reload-plugins` (or `--plugin-dir`) and `/agents` are part of the phase's
  eval, not an afterthought: a directory that scaffolds but does not register is the
  failure the phase-by-phase split exists to catch early.

## Update the ledger

In the same commit as the phase: the row's status `done`, the eval log file names — each
with its iteration directory when it came from `run-evals` (`<log>.md` ·
`evals/workspace/<target>/iteration-N`) — and a Notes cell with anything the next chat must
know that its note does not say. The Commit cell cannot hold its own SHA, so it holds the message prefix `(phase N)`; the **next** chat,
in step 4 of *Find the work*, resolves every `done` row that has a prefix and no SHA with
`git log --format=%h --grep='(phase N)'` and writes the SHA in its own commit. Phase 0's
SHA is written the same way by phase 1's chat.

## Stop

Print the ledger row as committed and the name of the next phase. Do not start it. If
context ran out before the phase could finish: set the row to `in progress`, list every
uncommitted path under Notes, commit nothing of the phase, and stop — the next chat resumes
from that list.
