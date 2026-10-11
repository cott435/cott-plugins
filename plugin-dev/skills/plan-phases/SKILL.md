---
name: plan-phases
description: Split an approved spec into phases and write the plan every phase is built from - a design (site/notes/{slug}/{slug}-design.md, from design-plugin), an edit list (site/notes/{slug}/{slug}-edits.md, from revise-plugin), or both. Reads the spec and nothing of the discussion behind it, asks about any gap it leaves, proposes the split (dependency levels, one owner per file region in a level) for approval, then writes an overview with every phase's scope and evals, a progress ledger, the eval sets (one writer subagent per target, in parallel) and every phase's note (one planner subagent per phase, a level at a time, then a unify agent, then your answers to what the planners could not decide, in one round). Commits them as phase 0. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), in a fresh chat on the branch design-plugin or revise-plugin created.
argument-hint: "<slug>"
disable-model-invocation: true
---

# Planning in phases

A change too big for one chat is built in phases, each one agent's work and each leaving the
plugin in a working state. This skill writes the whole plan before any of it starts: an
overview that says what each phase owns and how it is proved, eval sets fixed before any code
they test is written, a note per phase that says exactly what it builds, and a ledger that
says which phase is next. `run-phase` does the phases, one per agent, from their notes.

It starts from the spec an earlier chat committed, and deliberately from nothing else:

| Spec | Written by | Mode | What a phase owns |
|---|---|---|---|
| `site/notes/<slug>/<slug>-design.md` | `design-plugin` | **new** or **change**, from its header | components and build-order lines |
| `site/notes/<slug>/<slug>-edits.md` | `revise-plugin` | **review** | edit-list items, by id |
| both | `revise-plugin`, then `design-plugin` for its **Needs a design** items | **review** | items by id, and the design's components |

The discussion or the review behind a spec is long; a planner that reads it plans from
half-remembered turns. A planner that reads only the spec plans from what was approved. When
it cannot plan a phase without guessing, the spec has a gap, and the gap is asked about
instead of filled in.

**This skill writes every phase's note**, one planner subagent per phase, a level of the
split at a time. A note written with the plan cites no line numbers: it anchors every edit on
text quoted from the file, and `run-phase` finds that text where it is when the phase runs. A
planner of a later level reads the notes of the earlier phases on its files, so it anchors on
the text as those phases leave it. What a planner cannot decide from the spec comes back as a
question, and every question of the plan is asked in one round, before anything is built, so
the phases run with nothing left to ask. The planning that used to open every phase — a third
of its time, in series — happens here, side by side.

`E` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/edits.py`. This skill makes one commit and
never pushes.

## Find the spec

1. Confirm this is a plugin subdirectory (`.claude-plugin/plugin.json` exists).
2. Find the spec in `site/notes/<slug>/`: `<slug>-design.md`, `<slug>-edits.md`, or both.
   With no slug, use the one folder that has a spec and no `<slug>-progress.md`. With none,
   stop: neither `design-plugin` nor `revise-plugin` has run.
3. With an edit list: `E check site/notes/<slug>/<slug>-edits.md --decided` must pass. An
   open decision is `revise-plugin`'s to ask, so stop and say which. When its **Needs a
   design** section has items and there is no design, stop: `design-plugin <slug>` runs
   first.
4. Confirm the branch: `git branch --show-current` equals the branch the spec names. If not,
   stop and say so; never switch branches on the user's behalf.
5. Confirm a clean tree: `git status --porcelain` is empty. Otherwise stop with the list.

## Read, and nothing else

- **A design**: in full.
- **An edit list**: never whole. `E index` gives every item on one line (id, mechanism,
  decision, dependencies, files, title). Print the sections a planner needs with
  `sed -n '/^## <name>/,/^## /p'`: **Goal**, **Decisions taken**, **Platform facts**,
  **Build order**, **What must not break**. Open an item with `E show <id>` only when its
  index line cannot tell you which phase it belongs in.
- The plugin's `CLAUDE.md` (its own rules: a three-file rule, a site order file) and its
  `contracts.yml`.
- **change** and **review**: the headings, not the bodies, of every file named under **What
  must not break** and of every file whose headings another file parses
  (`grep -n '^#' <file>`). These are what the overview's **Files other files parse** quotes;
  they are quoted from the files, not from the spec's paraphrase.
- `${CLAUDE_PLUGIN_ROOT}/skills/run-evals/references/eval-kinds.md`, the one list of eval
  kinds: `mechanical`, `load`, `behavioral`, `trigger`, `platform-fact`.
- `${CLAUDE_PLUGIN_ROOT}/skills/plugin-anatomy/references/`: for each component kind the spec
  adds or changes (`skills.md`, `agents.md`, `hooks.md`, `mcp.md`, `manifest.md`,
  `other.md`), its **How to test it** section; and `edge-cases.md`.
- **change** and **review**: each existing set `evals/sets/<target>.json` the spec names, by
  its ids and names only (`python3 -c "import json,sys;[print(e['id'],e['name']) for e in
  json.load(open(sys.argv[1]))['evals']]" evals/sets/<target>.json`). The eval writers read
  the sets whole.

Do not read other plans' notes, the bodies of the plugin's agents and skills, findings files,
or any earlier conversation. If the user pastes part of the discussion, say that the spec is
the source and ask what it is missing.

## Find the gaps first

Walk the spec as the planners will meet it: for each phase you are about to propose, could a
planner that has read the spec, the overview and the files as they are write that phase's
note without a decision that is the user's? What it could not sorts into two kinds:

- **Detail left to the phase.** The text an edit anchors on, the order of steps inside a
  phase, a helper's name. The planner settles these in the note; that is its job.
- **A decision the spec did not take.** A horizon, a default, who reads a file, what an
  evaluator does on its second rejection. Ask about all of them in one `AskUserQuestion`
  round, with the recommended option first, and write each answer into one **Decisions
  taken** table with Origin *planning*: the edit list's when there is one, even with a
  design beside it, under the next `D-` id with the items it touches in its Items cell, so
  `edits.py show` prints it beside those items; otherwise the design's. A design read beside
  an edit list keeps its table as approved. If an answer would change a chart, a loop
  or a file where loops meet, stop instead: say the design needs reopening, name what, and
  leave it to the user. This skill does not redraw an approved chart.

## Rules for the split

The spec's **Build order** is the starting point: its dependencies order the phases, and its
smallest end-to-end slice is phase 1.

- **A phase is mergeable on its own.** The branch is releasable at every boundary: no phase
  leaves an agent citing a heading nobody writes yet. A skill that needs a later phase's file
  is created in that later phase, not stubbed. In **new** mode this means phase 1 is the
  smallest thing that is a working plugin (the one loop and the thinnest workflow that uses
  it, plus a README that describes only what exists), and every later phase adds to a bundle
  that already loads and builds.
- **A phase is one agent's work, and the split is by file, not by concept.** From an edit
  list, `E split site/notes/<slug>/<slug>-edits.md [--shared <glob>]…` prints the proposal:
  the items in dependency levels from their `depends:`; the items of one level that cite the
  same region of a file not shared in one phase; small clusters packed up to a cap of 9 (a
  hook or script item weighs 3, any other 1); a cluster over the cap cut into a sequence of
  phases; each phase depending on the phases that own what its items depend on. The **Level**
  column is the planning wave: two phases of one level cite no region of a file that is not
  shared, so their notes are written side by side. The shared files are the registries every
  phase adds to and that make no two phases one — `contracts.yml`, `README.md`,
  `CHANGELOG.md`, `hooks/hooks.json`, `evals/README.md`, `site/site.yml`, `site/flow.md`,
  `site/workflows/*`, `.claude-plugin/plugin.json`; the plugin's own (a fixture README, a
  test file every phase extends) go on the command's `--shared` and on the overview's
  `**Shared files:**` line, which `E coverage` and `P notes-check` read. From a design, do
  the same by hand: a level per **Build order** line, one phase per component or group of
  components that share no file, the same cap, each phase's **Files** named. Change the
  proposal where you know better — `--cap`, `--near`, a cluster split by hand into lettered
  items — and say why in chat. A phase that one item puts over the cap stays whole.
- **Ordered by dependency**, foundations first. A loop and the format of the file it writes go
  before the loops that read that file, with the thinnest workflow that uses a loop shipped in
  the same phase, so every phase ends with something a user can type. Scripts and their
  fixtures go before the prose that relies on them. An evaluator ships with or right after the
  unit it checks, never at the end. The phases table names each phase's dependencies
  explicitly; `E split` prints them from the items'.
- **review: every item in exactly one phase.** The Items cell lists ids and ranges
  (`E-001, E-004–E-009`). An item that has to land in two phases is split in the edit list
  into lettered items (`E-046a`, `E-046b`, the second depending on the first), each a whole
  block, the parent removed; that edit rides in this skill's commit. `E coverage` checks it.
- **Suggestions accepted in a design** get their own phases, or are named as optional
  additions to one, and nothing in the core depends on them.
- **Phase 0 is this skill's commit**: the overview, every phase's note, the eval sets and the
  ledger, plus the spec's *assumed* platform facts as platform-fact evals, which `run-phase`
  runs first.
  When the spec assumes no facts, this commit is the whole of phase 0, and its ledger row is
  written `done`. When it assumes any, the row is `in progress` with the evals listed under
  Notes, and the first `run-phase` chat runs them and marks it `done`.
- **The last phase is always** the end-to-end eval, the last checkpoint (below),
  the docs (`README.md`, `site/flow.md` and the `flow:` block of `site/site.yml` it is drawn
  from, `site/workflows/`, `CHANGELOG.md`'s unreleased section), and the release *proposal*: a bump
  at the level **What must not break** implies, or, for a new plugin, tagging `0.1.0` as
  scaffolded. `bump-version` decides on a yes; never this skill or `run-phase`.
  **review**, when the plugin has an audit ledger: the last phase also records a Fix attempt
  for every issue an item `closes:`, through `scripts/issues.py fix` in the shape of
  `fix-issues`' §6, its `--commit` the commit of the phase that landed the item (from the
  ledger). One place, after every item has landed, so no phase needs a second commit.
- **Every phase has eval rows** in the overview's **Evals by phase** table: `| Phase | ID |
  Kind | Target | Baseline | Set evals | Pass bar |`.
  - Kind is one of `run-evals`' kinds. Choose from `eval-kinds.md`, not from memory.
  - A behavioral row names `evals/sets/<target>.json` and eval IDs, which the eval writers put
    into that set in the phase-0 commit (see **The evals**). Trigger sets are the exception:
    the phase that adds a model-invoked skill writes its `<target>.trigger.json`, since it needs
    the final description.
  - **A phase is mechanical unless it is a checkpoint** (`eval-kinds.md`, **When behavioral
    evals run**). Every phase carries the mechanical rows for what it changes: fixtures,
    `check-contracts`, a line count, a load check. `build-site` is a row of the last phase
    only: the built site is not committed, so one build once the phases are in says what a
    build per phase would.
  - **A target's behavioral evals run once, after its last edit**: every id of that target,
    new or existing, in one row pair at the first checkpoint at or after the last phase that
    touches the target or what it is made of. `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phases.py
    touch <slug>` prints that phase per target from an edit list's `files:` (an upper bound:
    an item also lists lines it only cites); for a design, work it out from the Phases
    table's components. A new eval's row has Baseline `previous` (or `none`, or a ref) and
    runs compared; the existing ids' row has Baseline `working tree only`.
  - **Checkpoints are the phases where targets finish.** The last phase is always one. Name
    an earlier phase a checkpoint when targets finish there, so their result does not wait
    for the end; `phases.py plan-check` warns when a finished target waits more than three
    phases. The overview names them on one line under **Evals by phase**:
    `**Checkpoints:** 9, 14`. A flag every eval run of the plan needs — a baseline ref when
    the sets mix baselines — goes on a second line, `**Init flags:** --baseline <ref>`, and
    `phases.py brief` puts it on every `init` command it prints. A check every phase runs
    before its commit — the plugin's own fixture runner, its test file — goes on a third,
    each command as a code span, run from the plugin's directory:
    ``**Checks:** `python3 evals/fixtures/check_all.py` ``. `phases.py checks` runs them
    beside `check-contracts` in one call, and `finish` refuses the phase
    until they have passed on the tree it commits. A behavioral row's **Set
    evals** cell is `` `evals/sets/<target>.json` `` and its ids (`1, 4–6`), exactly: the
    command is built from it. An edit-list item's `evals:` names ids to rerun and new evals
    to write; both go in the row of their target's checkpoint.
  - A row says `blind` in its pass bar only where the change is meant to make an output
    better in a way no expectation states. Never by default.
  - A script item's `fixture:` is a mechanical row: the fixture's input and expected output.
  - The pass bar can be checked without judgment (default: every expectation passes and,
    where a baseline ran or was reused, the target's pass rate ≥ the baseline's).
- **Each component's own tests.** A phase that adds or changes a component takes its
  mechanical and load rows from the **How to test it** table in that component's
  `plugin-anatomy` reference: a hook gets its script piped recorded events and a `/hooks`
  check, an MCP server a `/mcp` check, not only a listing of skills and agents.
- **Every phase touching an agent or skill** runs the plugin's own rules, `check-contracts`
  (once a `contracts.yml` exists; in **new** mode, phase 1 creates it with the first claim the
  README makes about the bundle and a `frontmatter` claim for each of `skills/*/SKILL.md` and
  `agents/*.md` it ships), then its eval rows through `run-evals`. The last phase also
  runs `build-site`.
- **Every platform-fact row** says, in its pass bar, where its result is written back in
  `plugin-anatomy`.

## Show the split, then wait

In chat, not as a page, show one table: Phase · Level · What it adds · Items (**review**) or
Components (**new**, **change**) · Files · Depends on · Evals (kinds, and roughly how many
tokens for the behavioral and trigger rows, from the cost table in `eval-kinds.md`, with
*checkpoint* on the phases that are one and *mechanical* on the rest). Under the table: how
many phases and how many levels, `E split`'s warnings and what you did about each, and the
plan's total for the behavioral rows, in tokens, so the split is approved with its cost in
view. Then list any gap answers you wrote into the spec. Then ask with one
`AskUserQuestion`: approve the split, or change it (the user says what). Discuss, revise and
re-show the whole table until it is approved. Nothing is written before that.

## What is written

All under `site/notes/<slug>/`, so the site builder renders them under Notes, beside the spec:

| File | From template | Holds |
|---|---|---|
| `<slug>-00-overview.md` | `templates/phases/overview.md` | what changes, at a glance; the contents tree; files other files parse; the phases table, each row's level, scope, items, files and dependencies; every phase's eval rows |
| `<slug>-NN-<name>.md`, one per phase | `templates/phases/phase.md` | the phase's decisions, its files, the exact specification anchored on quoted text, its steps, its eval rows copied, and what done looks like; written by its planner, per **The notes** |
| `<slug>-progress.md` | `templates/phases/progress.md` | one row per phase: status, commit, eval logs, notes for the next chat |
| `evals/sets/<target>.json` and harness sheets | `run-evals`' set shape | the prompts and expectations every behavioral row runs |

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/phases/`. Copy the headings, and fill every
one or delete it with a line saying why. The why, the workflows, the decisions and the
non-goals stay in the spec; the overview points to it rather than copying it.

### The overview carries what crosses phases

A phase's note is written by a planner that sees only its own phase, and read by an agent
that sees only its own phase. So everything one phase's work depends on from another phase
is in the overview, exactly:

- **The Phases table**: per phase, the note's name (`NN-<name>`), its level, what it adds in
  one line, its Items (**review**: ids and ranges; **new** and **change**: the components and
  build-order lines it builds), the files it owns, and its dependencies. Everything not in a
  phase's Files cell, but for the shared files, is another phase's.
- **Files other files parse**: every heading, field or column one phase writes and a file in
  another phase reads, named exactly, with the phase that writes it and the phases that read
  it. A note may not rename anything in this table; a rename is a Deviation.
- **Evals by phase**: every phase's rows, as above. The planner copies its phase's rows into
  the note's **Evals** and may not loosen a pass bar; `P notes-check` compares them.

## The notes

Every phase from 1 up gets its note here, once the overview and the ledger are written and
`E coverage` and `P plan-check` pass, and before the eval sets: a planner may find a gap the
sets must know about.

**One planner per phase, a level at a time.** For each level of the Phases table in order,
spawn one general-purpose subagent per phase of that level, all in one message (a level of
more than ten phases goes in two), each given the prompt in `references/unit-planner.md`, and
wait for every one of them before the next level. A planner reads `P brief <slug> --phase N`
— the row, the eval rows, the spec's sections, the items with their cited lines as they
stand, the other phases on its files — the notes of the earlier phases the brief names on its
files, the component references its items need, and the files its phase owns, as they are
now; and it writes exactly `site/notes/<slug>/<slug>-NN-<name>.md`. It settles what the spec
left to the phase and returns, as *asked*, what is the user's. Planners of one level share no
file region, so none waits on another. When a level has returned: `P notes-check <slug>`.
A missing note is its planner respawned once with the lines that name it; two notes of one
level on one file is a split to redo (an item moved, or the file named shared and why).

**Then the unify pass.** One general-purpose subagent with the prompt in
`references/unify.md`. It reads every note's Decisions, Files and Specification and the
overview's **Files other files parse**, and makes the names agree where notes meet: a module
one phase creates and a later one imports, a heading one writes and another reads, two
phases adding a row to one shared table, a helper two notes each invent. It edits the notes
and that one table, runs `notes-check` until it prints `ok`, and returns what it changed and
every question the planners returned, deduplicated.

**Then the questions, in one round.** Every *asked* and *unresolved* line is the user's: ask
them all in one `AskUserQuestion` round, the recommended option first, as **Find the gaps
first** says; write each answer into the spec's **Decisions taken** with Origin *planning*,
and into the Decisions of the notes that asked, by hand. An answer that would change a
chart, a loop or a file where loops meet stops the plan, as there.

## The evals

The behavioral rows name their targets and eval IDs, but the sets do not exist yet. Writing
them is one job per target, and the targets are independent, so they are written in parallel.
Spawn one general-purpose subagent per target that has a behavioral row, **all in one
message**, each given the prompt in `references/eval-writer.md`. Each writer reads the spec,
the overview's rows for its target, `eval-kinds.md` and `run-evals`' set shape, and writes that
one set and its harness sheets.

Then check what came back before committing it. For each set:

- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/run-evals/scripts/eval_workspace.py validate
  evals/sets/<target>.json` exits 0;
- every eval ID an overview row names exists in the set, and nothing else was added to it;
- every expectation is observable in `outputs/` or the transcript, and at least one per new
  eval could fail against the row's baseline. A new eval whose every expectation the
  baseline already meets proves nothing about the phase;
- a changed target's set keeps its existing evals, with the new ones appended with `added_in:
  "<slug> phase 0, run from phase N"`.

Fix a failing set yourself, or give its writer the list and respawn it, once. A set still
wrong after that is reported in chat rather than committed.

## No ambiguity

The overview is written for a planner that has read only the spec, the overview and its own
phase's files, and for a builder that has read only those and its note. So it carries exact
paths for every file a phase owns; exact heading, field and column names for anything another
phase parses; each phase's items or components; every eval row and its pass bar; and the
commit-message prefix. A sentence that starts "consider" or "if
appropriate" is a decision not taken: take it, or ask it as a gap.

## Steps

1. Find the spec and read, per **Find the spec** and **Read, and nothing else**.
2. Find the gaps and ask about them, per **Find the gaps first**. Stop if a design needs
   reopening.
3. Split, per **Rules for the split** (**review**: from `E split`'s proposal), and get the
   split approved, per **Show the split, then wait**. Nothing below runs before that.
4. Write the overview, then the ledger: phase 0 `done` when there are no platform-fact evals,
   otherwise `in progress` with their IDs under Notes; every other row `todo`.
5. **review**: `E coverage site/notes/<slug>/<slug>-edits.md site/notes/<slug>/<slug>-00-overview.md`
   prints `ok`: every item in one phase, its dependencies reachable, no file region owned by
   two phases of one level. Fix the overview's Items, Files, Level or Depends on cells until
   it does. Then, for every plan, `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phases.py plan-check <slug>`
   exits 0: every behavioral row sits in a checkpoint and the last phase is one. Read its
   warnings: a row placed before a phase the edit list has touching its target moves to the
   later checkpoint unless that phase only cites the file.
6. Write the notes, per **The notes**: the planners, a level at a time, with `P notes-check`
   after each level; the unify agent; the questions in one round, their answers written into
   the spec and the notes. `P notes-check <slug>` exits 0 at the end.
7. Write the eval sets through the writers and check them, per **The evals**.
8. If the plugin has a `contracts.yml`, run `check-contracts`. `site/notes/<slug>/` is in its
   scope, so an overview or a note that quotes a forbidden pattern must scope the pattern
   with `files:` or be reworded. Fix the note, not the claim.
9. Commit the overview, every note, the eval sets, the ledger, any gap answers added to the
   spec, and any item split in the edit list: `<plugin> <slug> (phase 0): plan, notes and
   evals for <what>`. This is the only commit this skill makes, and it pushes nothing.
10. Print, for the user to paste into the next chat:

    > Branch `<plugin>-<slug>`. Run `/plugin-dev:run-phase <slug>` from `<plugin>/`, or
    > `/plugin-dev:run-phases <slug>` to run them all from one chat.

    And say how many phases and levels there are, how many questions were asked and answered,
    and whether the next chat starts with phase 0's platform-fact evals or, with none, with
    phase 1.
