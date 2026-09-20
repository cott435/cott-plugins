---
name: run-phase
description: Do the next unfinished phase of a plan written by plan-phases - a change to a plugin or a new plugin being built up - read the overview, the progress ledger and that phase's note, make exactly its edits, run the plugin's checks and the phase's evals, log them, commit once, update the ledger, and stop. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), one phase per Claude Code chat, typed by the user.
argument-hint: "[slug]"
disable-model-invocation: true
---

# Running one phase

A phase is one chat's worth of work, specified in a note a previous chat wrote. This chat
reads three files, does what the note says, proves it with the note's evals, commits once,
records where things stand, and stops — the next chat starts from the ledger, not from a
summary of this one.

## Find the work

1. Confirm this is a plugin subdirectory (`.claude-plugin/plugin.json` exists).
2. Locate the ledger: `site/notes/<slug>-progress.md`. With no slug argument and exactly one
   ledger, use it; with several, ask which. With none, stop — `plan-phases` has not run.
3. Confirm the branch: `git branch --show-current` equals the branch the ledger names. If
   not, stop and say so; never switch branches on the user's behalf.
4. Confirm a clean tree: `git status --porcelain` is empty, or every listed path is one the
   ledger's `in progress` row names under Notes. Anything else stops with the list.
5. Resolve SHAs: for every `done` row whose Commit cell is a `(phase N)` prefix, replace it
   with `git log --format=%h --grep='(phase N)'`. This edit rides in this chat's commit.

## Read, in this order, and nothing else up front

1. `site/notes/<slug>-00-overview.md` — the whole change, the phases table, the breaking
   changes.
2. `site/notes/<slug>-progress.md` — the first row whose status is not `done` is this
   chat's phase. `in progress` means a previous chat stopped mid-way: read its Notes cell
   and `git status`, and finish rather than restart.
3. That phase's note, `site/notes/<slug>-NN-<name>.md`.

The note names every plugin file to open; open those as the steps reach them. Do not read
the other phase notes, the evals of other phases, or any earlier conversation — the
overview carries what they concluded, and a later phase's note is not this chat's job.

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
- **The plugin's own rules.** Its `CLAUDE.md` — a three-file rule, a naming list, a site
  order file — applies to every file the phase adds or removes, in the same commit.
- **Checks before evals.** If the plugin has `contracts.yml`, `check-contracts` passes. If
  it has `site/`, `build-site` runs. Both before the evals, so a failed contract is fixed in
  the file rather than discovered by an eval.
- **Evals, through `run-evals`.** For each target in the note's `## Evals` table, invoke
  `run-evals` with that target's rows — the set file, the eval IDs, the baseline — in the
  table's order (platform facts and mechanical rows first). Every result is logged with
  `log-eval` before it is reported here, a clean pass exactly like a failure, with the
  commit field reading *uncommitted — see working-tree diff*, since the phase's commit
  comes after.
- **Stop for review.** When any row is behavioral, stop once the viewer is open (or the
  results table is in chat, if skill-creator is missing) and wait for the user. Read
  `feedback.json` before continuing. Nothing is committed before the user has replied.
  Feedback asking for a change within the note's Files — or within the eval sets this
  phase ran, per the exception above — is part of this phase; anything else is a
  *noticed:* line in the ledger.
- **One fix, then a Deviation.** A missed pass bar: one fix inside the note's Files, rerun
  that target's rows as the next iteration, review again. Still missed: append the outcome
  — the bar, the result, what was tried — to `## Deviations` and ask whether to commit.
- **Notes written before 0.9** have no `## Evals` section; run the evals their Steps list
  names, as that list describes, and write "old-format note" in the ledger's Notes cell.
- **Deviations are written down.** Where the note could not be followed as written — a
  heading did not exist, a platform fact came out differently, a step was wrong — append a
  `## Deviations` section to the note (what the note said, what was done, why) and, if a
  later note's assumption is now false, one line in the ledger's Notes cell for that later
  phase. Never silently do something other than the note.
- **One commit.** All of the phase's edits, the eval logs, the note's Deviations section,
  and the ledger row, staged by explicit path. Message from the note, in the form
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
