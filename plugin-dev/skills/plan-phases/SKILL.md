---
name: plan-phases
description: Split an approved design - site/notes/{slug}-design.md, written by design-plugin - into phases, each sized for one Claude Code chat. Reads the design and nothing of the discussion behind it, asks about any gap the design leaves, proposes the phase split for approval, then writes an overview, one note per phase with its own evals table, the eval sets (one writer subagent per target, in parallel) and a progress ledger that run-phase reads. Commits them as phase 0. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), in a fresh chat on the branch design-plugin created.
argument-hint: "<slug>"
disable-model-invocation: true
---

# Planning in phases

A design too big for one chat is built in phases, each small enough for one chat and each
leaving the plugin in a working state. This skill writes the split down before any of it
starts: notes a fresh chat can read cold, eval sets that prove each phase, and a ledger that
says which phase is next. `run-phase` does the phases, one per chat.

It starts from the design `design-plugin` committed, `site/notes/<slug>-design.md`, and
deliberately from nothing else. The discussion that produced the design is long; a planner
that reads it plans from half-remembered turns. A planner that reads only the design plans
from what was approved. When it cannot write a phase note without guessing, the design has a
gap, and the gap is asked about instead of filled in.

This skill writes the notes, the eval sets and the ledger, and makes one commit. It is typed
by the user and never pushes.

## Find the design

1. Confirm this is a plugin subdirectory (`.claude-plugin/plugin.json` exists).
2. Read `site/notes/<slug>-design.md`. With no slug and exactly one `*-design.md` that has no
   `<slug>-progress.md` beside it, use that one. With none, stop: `design-plugin` has not run.
3. Confirm the branch: `git branch --show-current` equals the branch the design names. If not,
   stop and say so; never switch branches on the user's behalf.
4. Confirm a clean tree: `git status --porcelain` is empty. Otherwise stop with the list.
5. Take the mode (**new** or **change**) from the design's header line.

## Read, and nothing else

- The design, in full.
- The plugin's `CLAUDE.md` (its own rules: a three-file rule, a site order file) and its
  `contracts.yml`.
- **change:** every agent and skill file the design's **Components** table marks as changed
  or removed, and every file named under **What must not break**. Quote headings and rules
  from the files, not from the design's paraphrase of them.
- `${CLAUDE_PLUGIN_ROOT}/skills/run-evals/references/eval-kinds.md`, the one list of eval
  kinds: `mechanical`, `load`, `behavioral`, `trigger`, `platform-fact`.
- `${CLAUDE_PLUGIN_ROOT}/skills/plugin-anatomy/references/`: the file for each component kind
  the design's **Components** table uses (`skills.md`, `agents.md`, `hooks.md`, `mcp.md`,
  `manifest.md`, `other.md`), and `edge-cases.md`. These are where frontmatter fields, file
  shapes and each kind's tests come from; the design's paraphrase is not.
- **change:** the existing set `evals/sets/<target>.json` of every target the design changes.

Do not read other plans' notes or any earlier conversation. If the user pastes part of the
discussion, say that the design is the source and ask what it is missing.

## Find the gaps first

Before splitting, walk the design as the note-writer will: for each component and each file in
**How they fit together**, could a phase note give its exact path, its frontmatter, the
headings its readers parse, and an eval with a pass bar, without guessing? What cannot be
written sorts into two kinds:

- **Detail the design leaves to planning.** Exact heading names, frontmatter fields, the order
  of steps inside a phase. Decide these in the phase notes; that is this skill's job.
- **A decision the design did not take.** A horizon, a default, who reads a file, what an
  evaluator does on its second rejection. Ask about all of them in one `AskUserQuestion`
  round, with the recommended option first, and write each answer into the design's
  **Decisions taken** with Origin *planning*. If an answer would change a chart, a loop or a
  file where loops meet, stop instead: say the design needs reopening, name what, and leave it
  to the user. The charts were approved as drawn, and this skill does not redraw them.

## Rules for the split

The **Build order** section is the starting point: its dependencies order the phases, and its
smallest end-to-end slice is phase 1.

- **A phase is mergeable on its own.** The branch is releasable at every boundary: no phase
  leaves an agent citing a heading nobody writes yet. A skill that needs a later phase's file
  is created in that later phase, not stubbed. In **new** mode this means phase 1 is the
  smallest thing that is a working plugin (the one loop and the thinnest workflow that uses
  it, plus a README that describes only what exists), and every later phase adds to a bundle
  that already loads and builds.
- **A phase fits one chat.** One concept; at most six or so files edited; at most one new agent
  or two new skills. Two independent small items may pair; nothing else does.
- **Ordered by dependency**, foundations first. A loop and the format of the file it writes go
  before the loops that read that file, with the thinnest workflow that uses a loop shipped in
  the same phase, so every phase ends with something a user can type. An evaluator ships with
  or right after the unit it checks, never at the end. The phases table names each phase's
  dependencies explicitly.
- **Suggestions accepted in the design** get their own phases, or are named as optional
  additions to one, and nothing in the core depends on them.
- **Phase 0 is this skill's commit**: the notes, the eval sets and the ledger, plus the
  design's *assumed* platform facts as platform-fact evals, which `run-phase` runs first.
  When the design assumes no facts, this commit is the whole of phase 0, and its ledger row is
  written `done`. When it assumes any, the row is `in progress` with the evals listed under
  Notes, and the first `run-phase` chat runs them and marks it `done`.
- **The last phase is always** the end-to-end eval, the docs (`README.md`, `site/flow.md`,
  `site/workflows/`, `CHANGELOG.md`'s unreleased section), and the release *proposal*: a bump
  at the level **What must not break** implies, or, for a new plugin, tagging `0.1.0` as
  scaffolded. `bump-version` decides on a yes; never this skill or `run-phase`.
- **Every phase has an `## Evals` table**: `| ID | Kind | Target | Baseline | Set evals | Pass
  bar |`.
  - Kind is one of `run-evals`' kinds. Choose from `eval-kinds.md`, not from memory.
  - A behavioral row names `evals/sets/<target>.json` and eval IDs, which the eval writers put
    into that set in the phase-0 commit (see **The evals**). Trigger sets are the exception:
    the phase that adds a model-invoked skill writes its `<target>.trigger.json`, since it needs
    the final description.
  - A phase that changes a target with an existing set reruns that set as regression, as its
    own row.
  - The pass bar can be checked without judgment (default: every expectation passes and the
    target's pass rate ≥ the baseline's).
- **Each component's own tests.** A phase that adds or changes a component takes its
  mechanical and load rows from the **How to test it** table in that component's
  `plugin-anatomy` reference: a hook gets its script piped recorded events and a `/hooks`
  check, an MCP server a `/mcp` check, not only a listing of skills and agents.
- **Every phase touching an agent or skill** runs the plugin's own rules, `check-contracts`
  (once a `contracts.yml` exists; in **new** mode, phase 1 creates it with the first claim the
  README makes about the bundle and a `frontmatter` claim for each of `skills/*/SKILL.md` and
  `agents/*.md` it ships), and `build-site`, then its Evals table through `run-evals`.
- **Every platform-fact row** says, in its pass bar, where its result is written back in
  `plugin-anatomy`.

## Show the split, then wait

In chat, not as a page, show one table: Phase · What it adds · Depends on · Evals (kinds, and
roughly how many tokens for the behavioral and trigger rows, from the cost table in
`eval-kinds.md`) · May pair with. Under it, list any gap answers you wrote into the design.
Then ask with one `AskUserQuestion`: approve the split, or change it (the user says what).
Discuss, revise and re-show the whole table until it is approved. Nothing is written before
that.

## What is written

All under `site/notes/`, so the site builder renders them under Notes, beside the design:

| File | From template | Holds |
|---|---|---|
| `<slug>-00-overview.md` | `templates/phases/overview.md` | what changes, at a glance; the contents tree; files other files parse; the phases table with dependencies |
| `<slug>-NN-<name>.md`, one per phase from `01` | `templates/phases/phase.md` | purpose; decisions; files touched; the exact specification; steps; evals; done-when |
| `<slug>-progress.md` | `templates/phases/progress.md` | one row per phase: status, commit, eval logs, notes for the next chat |
| `evals/sets/<target>.json` and harness sheets | `run-evals`' set shape | the prompts and expectations every behavioral row runs |

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/phases/`. Copy the headings, and fill every
one or delete it with a line saying why. The why, the workflows, the decisions and the
non-goals stay in the design; the overview points to it rather than copying it.

### The phase note

Its sections, in order:

- **`# NN — <name>`**, then a purpose paragraph: what the phase adds and the gap it closes,
  written for a chat that has read only the design, the overview, the ledger and this note.
- **`## Decisions`**: anything settled here rather than in the design, each with its reason.
- **`## Files`**: a Path · Change table, one row per file the phase touches.
- **`## Specification`**: the exact content. Frontmatter, heading names, rules,
  `contracts.yml` entries, and any prompt another model will be given, verbatim. Frontmatter
  uses only the keys in the component's `plugin-anatomy` reference, and the note names that
  reference beside each new component.
- **`## Steps`**: ordered so the bundle is consistent after each one.
- **`## Evals`**: the table described under **Rules for the split**.
- **`## Done when`**: conditions checkable without judgment.
- **`## Deviations`**: appended by `run-phase` when the note could not be followed as written.
  This skill never writes it.

`references/example-phase.md` walks through a real one.

## The evals

Once every phase note is written, the behavioral rows name their targets and eval IDs, but the
sets do not exist yet. Writing them is one job per target, and the targets are independent, so
they are written in parallel. Spawn one general-purpose subagent per target that has a
behavioral row, **all in one message**, each given the prompt in `references/eval-writer.md`.
Each writer reads the design, the notes whose rows name its target, `eval-kinds.md` and
`run-evals`' set shape, and writes that one set and its harness sheets.

Then check what came back before committing it. For each set:

- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/run-evals/scripts/eval_workspace.py validate
  evals/sets/<target>.json` exits 0;
- every eval ID a note's row names exists in the set, and nothing else was added to it;
- every expectation is observable in `outputs/` or the transcript, and at least one per eval
  could fail against the row's baseline. A set whose every expectation the baseline already
  meets proves nothing about the phase;
- a changed target's set keeps its existing evals, with the new ones appended with `added_in:
  "<slug> phase 0, run from phase N"`.

Fix a failing set yourself, or give its writer the list and respawn it, once. A set still
wrong after that is reported in chat rather than committed.

## No ambiguity

Each phase note is written for a model that has read only the design, the overview, the ledger
and that note. So it carries exact file paths; exact frontmatter blocks for new agents and
skills; exact heading and column names for anything another file parses; the `contracts.yml`
entries that will enforce them; the eval and its pass condition; the commit message; and a
**Done when** a reader can check without judgment. A sentence that starts "consider" or "if
appropriate" is a decision not taken: take it, or ask it as a gap.

## Steps

1. Find the design and read, per **Find the design** and **Read, and nothing else**.
2. Find the gaps and ask about them, per **Find the gaps first**. Stop if the design needs
   reopening.
3. Split, per **Rules for the split**, and get the split approved, per **Show the split, then
   wait**. Nothing below runs before that.
4. Write the overview, then one note per phase, then the ledger: phase 0 `done` when there are
   no platform-fact evals, otherwise `in progress` with their IDs under Notes; every other row
   `todo`.
5. Write the eval sets through the writers and check them, per **The evals**.
6. If the plugin has a `contracts.yml`, run `check-contracts`. `site/notes/` is in its scope,
   so a note that quotes a forbidden pattern must scope the pattern with `files:` or be
   reworded. Fix the note, not the claim.
7. Commit the notes, the eval sets, the ledger and any gap answers added to the design:
   `<plugin> <slug> (phase 0): phase notes and evals for <what>`. This is the only commit this
   skill makes, and it pushes nothing.
8. Print, for the user to paste into the next chat:

   > Branch `<plugin>-<slug>`. Run `/plugin-dev:run-phase <slug>` from `<plugin>/`.

   And say how many phases there are, which may pair in one chat, and whether the next chat
   starts with phase 0's platform-fact evals or, with none, with phase 1.
