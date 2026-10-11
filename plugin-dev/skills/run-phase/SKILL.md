---
name: run-phase
description: Do the next unfinished phase of a plan written by plan-phases - a change to a plugin, a new plugin being built up, or a reviewed plugin's edit list - read the spec, the overview and the progress ledger through phases.py, read that phase's note (written with the plan; or write it first, for a plan from before notes were written there), find its anchors in the files as they are now, make exactly its edits, run the plugin's checks and the phase's evals, log them, commit once, update the ledger, and stop. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), one phase per Claude Code chat, typed by the user.
argument-hint: "[slug]"
disable-model-invocation: true
---

# Running one phase

A phase is one agent's work. `plan-phases` fixed what it owns and how it is proved, in the
overview, and wrote its note: the decisions, the files, the exact specification, the steps.
This chat finds the note's anchors in the files as they are now, does what the note says,
proves it with the overview's evals for the phase, commits once, records where things stand,
and stops. The next chat starts from the ledger, not from a summary of this one.

The note cites no line numbers: it anchors every edit on text quoted from the file, because
the phases before this one move lines, and this chat finds the text where it is. A plan from
before `plan-phases` wrote the notes has none; then this chat writes the phase's note first,
per **A phase with no note**.

`E` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/edits.py`.

## Find the work

`P` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phases.py`, run from the plugin's
directory. It reads the ledger and the overview so this chat does not, and it decides by
exit code what a chat would otherwise decide by reading.

1. `P next [slug]`. Exit 0 prints the phase to do on one line. Exit 1 prints what stops it —
   not a plugin directory, no ledger (`plan-phases` has not run), several plans (ask which),
   the wrong branch, a tree that is not clean — and this chat stops with that line; it never
   switches branches or cleans a tree on the user's behalf. Exit 3: the plan is done.
2. `P brief [slug]`. Its output is this chat's copy of the plan: the phase's row from the
   overview's Phases table, its eval rows, whether it is a checkpoint, its ledger row with
   the notes earlier chats left for it, the overview's conventions, and a `sed` line for
   each other section of the overview. It also marks the phase as begun.

## Read, in this order, and nothing else up front

1. The spec, for the why:
   - `site/notes/<slug>/<slug>-design.md` when there is one: the workflows and their charts,
     the decisions, the non-goals, as approved. Plans written before `design-plugin` existed
     have none; their overview carries it.
   - `site/notes/<slug>/<slug>-edits.md` when there is one, never opened: `P brief` printed
     its **Goal**, **Decisions taken** and **What must not break** sections.
2. `P brief`'s output, in place of the overview and the ledger: read neither file whole.
   The overview's other sections (the contents tree, the files other files parse, the
   breaking changes) are read with the `sed` line the brief gives, when a step needs one.
3. A ledger row that says `in progress` means a previous chat stopped mid-way: read its
   notes in the brief and `git status`, and finish rather than restart. Phase 0 is the
   exception: `plan-phases` leaves it `in progress` on purpose when it has platform-fact
   evals, listed in its notes. Running those evals is this chat's phase; the overview is
   its note.
4. That phase's note, named in the brief's **Its note**: `site/notes/<slug>/<slug>-NN-<name>.md`,
   whole. It is the plan for this chat's edits. When the brief says the phase has no note (a
   plan from before `plan-phases` wrote them), this phase's items are printed under it
   whole, with the decisions they cite and, under each item, the lines its `files:` cites as
   they stand in the tree now (`E show … --located` prints the same for one item); then
   write the note, per **A phase with no note**.

The brief is most of the reading. What it does not show, read in as few messages as it
takes: every read that does not depend on another goes in the same message, never one per
turn. A phase's cost is its turns times its context, and the reading before the note was
most of a phase's turns.

Open plugin files as the note's steps reach them. Do not read other phases' notes or items,
the evals of other phases, findings files, or any earlier conversation: the spec and the
overview carry what they concluded, and another phase's work is not this chat's job. A
phase never edits the spec or the overview: where the note cannot follow them, the
disagreement is a Deviation.

## A phase with no note

Only when the brief says the phase has no note: a plan from before `plan-phases` wrote them.
The note is the plan for this chat's edits, written before any of them, and it rides in the
phase's commit, so the next reader sees what was planned beside what was done.

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
- **`## Evals`**: this phase's rows as `P brief` printed them, copied, columns
  `| ID | Kind | Target | Baseline | Set evals | Pass bar |`. A pass bar is never loosened
  here.
- **`## Done when`**: conditions checkable without judgment.

Against an edit list, each item's lines are where the review found them, and earlier phases
have moved them since. The brief carries each one across: under an item, `path:line → :line`
with the lines there, marked *moved*, *as reviewed*, or *changed since the review*. Cite the
line where it is now. A place marked *changed* is one an earlier phase edited: read it, and
when that phase already made the change, say so under Decisions and drop that edit; when the
text is gone for any other reason, the item cannot be followed as written, which is a
Deviation.

`references/example-phase.md` walks through a real note.

## Do the phase

Follow the note's **Steps** in order. Whatever the note says, these always apply:

- **Find every anchor first.** The note quotes text from the files as they stood when it was
  written. Before the first edit, `grep -nF` each quoted anchor in its file as it is now. One
  found once: edit there. One that moved: edit where it is. One that is gone because an
  earlier phase's commit already made this edit: say so under this note's `## Deviations`
  and drop the edit. One gone for any other reason: the edit cannot be made as written,
  which is a Deviation too, and the brief's **Other phases on this phase's files** says
  whose work moved it.
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
- **Checks before evals, in one call.** `P checks [slug]` runs the phase's whole mechanical
  gate — `check-contracts` when the plugin has `contracts.yml`, and the plan's own commands
  from the overview's `**Checks:**` line — and prints one line per command, a failure's FAIL
  lines under it. `build-site` is not part of a phase: `site/docs/` is not committed, so
  `checks` builds the site once, at the plan's last phase, and a phase before it never runs
  `build-site` on its own, whatever an older overview's rows say. A phase that changes how
  work flows still edits the hand-written `site/workflows/` page it changes, and the `flow:`
  block of `site/site.yml` when a role, a document or a driver changes, as its files. `P brief` names what it runs
  here. Run it once, when the edits are done and before the evals, as one foreground Bash
  call with `timeout: 600000`, so a failed contract is fixed in the file rather than
  discovered by an eval. A plan's suite can run for minutes, and a call left at the default
  timeout is cut off and run twice. Never start it in the background and never poll it: each
  look at a log is a turn that re-reads this chat's whole context. While editing, run only
  the cases you touched, with the checker they belong to. After a fix, `P checks` again;
  `P finish` refuses a plan with a `**Checks:**` line until it has passed on the tree as it
  stands. The note, the ledger and the eval logs may change after it.
- **Evals, through `run-evals`.** For each target in the note's `## Evals` table, invoke
  `run-evals` with that target's rows — the set file, the eval IDs, the baseline — in the
  table's order (platform facts and mechanical rows first). Most phases have mechanical rows
  only: behavioral rows sit in the plan's checkpoints, where each target's evals run once,
  after its last edit. `P brief` printed, under the rows, the exact `eval_workspace.py init`
  command for each behavioral row: its set, its ids, `--working-tree-only` where the row's
  Baseline cell says so, and the plan's own flags. Run those commands as printed; do not
  compose one from the row. `P finish` reads each iteration's manifest and refuses a phase
  where an id a row names was laid out in none of them, or a compared row ran one-sided. Every result is
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
  runner** says this eval needs it; plugin-dev's Agent guard refuses the spawn otherwise. No blind comparison unless a row's pass bar says
  `blind`.
- **A regression found at a checkpoint is this phase's to fix.** A checkpoint row's failed
  expectation that the baseline passes was broken by an earlier phase. Find it —
  `git log --oneline <the plan's branch point>..HEAD -- <target_path>`, then the diff
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
- **One commit, made by `P finish`.** `P finish [slug] --what "<what>" --log <eval log>…
  --iteration <iteration dir>… --notes "<for the next chat>"`, with `--also <path>` for each
  path outside the plugin the phase changed and `--trailer "<line>"` for each attribution
  line this session's commits carry. It refuses, naming each gap, unless the phase is whole:
  the note exists; every log exists and has its row in `evals/README.md`; `P checks` has
  passed on the tree as it stands, when the plan has a `**Checks:**` line; every behavioral
  row of the phase has its ids laid out, in the row's mode, in the iterations given, each
  with a report and no run left not run or not graded (`--skip-row <ID>` for a row a
  Deviation says was not run); `check-contracts` passes;
  nothing outside the plugin is changed and unnamed. Then it fills the ledger row, resolves
  earlier rows' `(phase N)` to SHAs, stages the plugin and commits
  `<plugin> <slug> (phase N): <what>`. Never write the ledger row or run `git commit` for a
  phase by hand: a phase committed around `finish` is checked when this chat stops, and the
  stop is refused until it stands. Nothing is pushed.
- **Never bump, never tag.** If the note says to propose a release — a bump at some level
  for a change, or tagging `0.1.0` as scaffolded for a new plugin — say so in chat with what
  the note names and stop; `bump-version` runs only on the user's yes.
- **A new plugin's phases build a bundle that must load.** After a phase that adds an agent
  or skill, `/reload-plugins` (or `--plugin-dir`) and `/agents` are part of the phase's
  eval, not an afterthought: a directory that scaffolds but does not register is the
  failure the phase-by-phase split exists to catch early.

## Update the ledger

`P finish` does it, in the phase's commit: the row's status `done`, the eval log names and
iteration directories it was given, and `--notes` as the Notes cell — anything the next chat
must know that its note will not say, and nothing else. The Commit cell cannot hold its own
SHA, so it holds `(phase N)`; the next phase's `finish` resolves it.

## Stop

Print what `P finish` printed: the commit and the next phase. Do not start it. If context
ran out before the phase could finish: set the row to `in progress` in the ledger by hand,
list every uncommitted path under Notes, commit nothing of the phase, and stop — the next
chat's `P next` accepts a tree whose paths that row names, and resumes from the list.
