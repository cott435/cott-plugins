---
name: plan-phases
description: Split an approved spec into phases and write the whole plan before any phase runs. The spec is a design (site/notes/{slug}/{slug}-design.md, from design-plugin), an edit list (site/notes/{slug}/{slug}-edits.md, from revise-plugin), or both. Reads the spec and nothing of the discussion behind it, asks about every gap it leaves, proposes the split (dependency levels; one owner per file in a level) for approval, then writes the overview, the ledger, every phase's note (one planner subagent per phase, a level at a time, then a unify agent, then your answers in one round) and the eval sets (one writer per target). One commit, phase 0. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json), in a fresh chat on the branch design-plugin or revise-plugin created.
argument-hint: "<slug>"
disable-model-invocation: true
---

# Planning in phases

A change too big for one chat is built in phases: one agent and one commit each, the plugin
working after every one. This skill writes the whole plan first, so the phases run with
nothing left to decide. It reads the spec an earlier chat committed, and deliberately nothing
else: a planner that reads the discussion plans from half-remembered turns; one that reads
only the spec plans from what was approved, and asks about what it cannot plan.

| Spec | Written by | Mode | A phase owns |
|---|---|---|---|
| `site/notes/<slug>/<slug>-design.md` | `design-plugin` | **new** or **change**, from its header | components and build-order lines |
| `site/notes/<slug>/<slug>-edits.md` | `revise-plugin` | **review** | edit-list items, by id |
| both | `revise-plugin`, then `design-plugin` for its **Needs a design** items | **review** | items by id, and the design's components |

`E` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/edits.py`; `P` is
`python3 ${CLAUDE_PLUGIN_ROOT}/scripts/phases.py`. This skill makes one commit and never
pushes.

## 1. Find the spec

1. `.claude-plugin/plugin.json` exists here. Otherwise stop: run from the plugin's directory.
2. The spec is in `site/notes/<slug>/`: `<slug>-design.md`, `<slug>-edits.md`, or both. With
   no slug, take the one folder that has a spec and no `<slug>-progress.md`. With none, stop:
   neither `design-plugin` nor `revise-plugin` has run.
3. With an edit list, `E check site/notes/<slug>/<slug>-edits.md --decided` passes. An open
   decision is `revise-plugin`'s to ask: stop and name it. Items under **Needs a design** with
   no design beside them: stop, `design-plugin <slug>` runs first.
4. `git branch --show-current` is the branch the spec names. Otherwise stop; never switch
   branches for the user.
5. `git status --porcelain` is empty. Otherwise stop with the list.

## 2. Read, and nothing else

- **A design**: whole.
- **An edit list**: never whole. `E index` prints every item on one line (id, mechanism,
  decision, dependencies, files, title). Print **Goal**, **Decisions taken**, **Platform
  facts**, **Build order** and **What must not break** with `sed -n '/^## <name>/,/^## /p'`.
  `E show <id>` only for an item whose index line does not say which phase it belongs in.
- The plugin's `CLAUDE.md` and `contracts.yml`.
- **change** and **review**: the headings (`grep -n '^#' <file>`), not the bodies, of every
  file under **What must not break** and of every file another file parses. The overview's
  **Files other files parse** quotes these from the files, not from the spec.
- `${CLAUDE_PLUGIN_ROOT}/skills/run-evals/references/eval-kinds.md`: the kinds `mechanical`,
  `load`, `behavioral`, `trigger`, `platform-fact`, and **When behavioral evals run**.
- `${CLAUDE_PLUGIN_ROOT}/skills/plugin-anatomy/references/`: **How to test it** in the file
  for each component kind the spec adds or changes (`skills.md`, `agents.md`, `hooks.md`,
  `mcp.md`, `manifest.md`, `other.md`), and `edge-cases.md`.
- **change** and **review**: the ids and names of every existing set `evals/sets/<target>.json`
  the spec names (`python3 -c "import json,sys;[print(e['id'],e['name']) for e in
  json.load(open(sys.argv[1]))['evals']]" <set>`). The eval writers read the sets whole.

Not other plans' notes, not the bodies of the plugin's agents and skills, not findings files,
not any earlier conversation. If the user pastes the discussion, say the spec is the source
and ask what it is missing.

## 3. Ask about the gaps

For each phase you are about to propose: could a planner that has read the spec, the overview
and the files write its note without taking a decision that is the user's? What it could not
is one of two things:

- **Detail left to the phase**: the text an edit anchors on, the order of steps, a helper's
  name. The planner settles it. Leave it.
- **A decision the spec did not take**: a horizon, a default, who reads a file, what an
  evaluator does on its second rejection. Ask every one in one `AskUserQuestion` round,
  recommended option first. Write each answer into **Decisions taken** with Origin
  *planning*: into the edit list's table when there is one (next `D-` id, the items it
  touches in its Items cell, so `E show` prints it beside them), otherwise the design's. A
  design read beside an edit list keeps its table as approved.

An answer that would change a chart, a loop or a file where loops meet stops the plan: say the
design needs reopening and name what. This skill does not redraw an approved chart.

## 4. The split

A phase is one agent's work on files no other phase of its level touches. Three things decide
the split:

1. **Level** is dependency depth. An item with no `depends:` is level 0; an item is one level
   below the deepest item it depends on. Phases of one level are planned side by side, so
   two of them never cite the same file. Phases are built in level order, lowest first.
2. **Phase** is the items of one level that cite the same file, merged until no two phases of
   the level share a file. Shared files never merge phases: `contracts.yml`, `README.md`,
   `CHANGELOG.md`, `hooks/hooks.json`, `evals/README.md`, `site/site.yml`, `site/flow.md`,
   `site/workflows/*`, `.claude-plugin/plugin.json`, plus the plugin's own registries (a
   fixture README, a test file every phase extends) named on the overview's
   `**Shared files:**` line.
3. **Size** is a cap of 9: a hook or script item weighs 3, any other 1. Small phases of one
   level pack together up to the cap. One over the cap becomes a sequence of phases, each its
   own level. A single item over the cap stays whole.

**review**: `E split site/notes/<slug>/<slug>-edits.md [--shared <glob>]…` prints this split
as the Phases table, Depends on filled from the items' `depends:`, with warnings. Change it
where you know better (`--cap`, `--near`, an item cut by hand into lettered items `E-046a`,
`E-046b`, the second depending on the first, each a whole block, the parent removed, the edit
riding in this commit) and say why in chat. Every item lands in exactly one phase; `E coverage`
checks that and the one-owner rule.

**new** and **change**: do the same by hand. A level per **Build order** line, a phase per
component or group of components sharing no file, the same cap, each phase's **Files** named.

Then fix the ends and the order:

- **Phase 1** is the smallest end-to-end slice. **new**: the smallest working plugin, one
  loop and the thinnest workflow that uses it, a README that describes only what exists,
  `CLAUDE.md`, and `contracts.yml` with the README's first claim and a `frontmatter` claim per
  `skills/*/SKILL.md` and `agents/*.md`.
- **Every boundary is mergeable.** No phase leaves an agent citing a heading nobody writes
  yet; a skill that needs a later file is created in that later phase, not stubbed. A loop
  and the format it writes go before the loops that read it, scripts and fixtures before the
  prose that relies on them, an evaluator with or right after the unit it checks.
- **Suggestions accepted in a design** get their own phase or are optional additions to one;
  nothing in the core depends on them.
- **Phase 0 is this commit**: overview, notes, eval sets, ledger, and the spec's *assumed*
  platform facts as platform-fact evals, which `run-phase` runs first. Its ledger row is
  `done` when there are no facts, else `in progress` with the eval ids under Notes.
- **The last phase** is the end-to-end eval, the last checkpoint, the docs (`README.md`,
  `site/flow.md` and the `flow:` block of `site/site.yml`, `site/workflows/`, `CHANGELOG.md`'s
  unreleased section), `build-site`, and the release *proposal*: a bump at the level **What
  must not break** implies, or `0.1.0` for a new plugin. `bump-version` decides on a yes,
  never this skill or `run-phase`. **review**, when the plugin has an audit ledger: it also
  records a Fix attempt for every issue an item `closes:`, through `scripts/issues.py fix` as
  `fix-issues` §6 shapes it, `--commit` the commit that landed the item.

## 5. The evals

Every phase has rows in the overview's **Evals by phase** table: `| Phase | ID | Kind |
Target | Baseline | Set evals | Pass bar |`. The rules:

- **Kind** is one of `eval-kinds.md`'s; read it, do not recall it.
- **Every phase is mechanical unless it is a checkpoint.** Each phase carries the mechanical
  rows for what it changes, taken from the component's **How to test it** table: a fixture, a
  hook's script piped recorded events and a `/hooks` check, an MCP server's `/mcp` check,
  `check-contracts`, a load check. A script item's `fixture:` is a mechanical row. The
  `build-site` row belongs to the last phase only.
- **A target's behavioral evals run once, after its last edit**: every id of the target, new
  and existing, in one row pair at the first checkpoint at or after the last phase that
  touches it or what it is made of. `P touch <slug>` prints that phase per target from an
  edit list (an upper bound: an item also lists files it only cites); from a design, read it
  off the Phases table. New ids: Baseline `previous`, `none` or a ref, run compared. Existing
  ids: Baseline `working tree only`.
- **Checkpoints** are the phases where targets finish, on one line under **Evals by phase**:
  `**Checkpoints:** 9, 14`. The last phase is always one; name an earlier one where targets
  finish early, so their result does not wait. `P plan-check` warns when a finished target
  waits more than three phases.
- **Two more lines there**, when needed. `**Init flags:** --baseline <ref>`: a flag every
  eval run of the plan needs, which `P brief` puts on every `init` command. ``**Checks:**
  `python3 evals/fixtures/check_all.py` ``: the plugin's own checks every phase runs before
  its commit, each a code span, run from the plugin's directory. `P checks` runs them beside
  `check-contracts`, and `P finish` refuses the phase until they pass on the tree it commits.
- **Set evals** is `` `evals/sets/<target>.json` `` and the ids (`1, 4–6`), exactly: the
  command is built from the cell. The writers put the new ids into that set in this commit.
  Trigger sets are the exception: the phase adding a model-invoked skill writes
  `<target>.trigger.json`, since it needs the final description. An item's `evals:` line names
  ids to rerun and evals to write; both go in its target's checkpoint row.
- **Pass bar** is checkable without judgment: every expectation passes and, where a baseline
  ran, the pass rate is not below it. `blind` only where the change should make an output
  better in a way no expectation states, never by default. A platform-fact row's pass bar
  says where its result is written back in `plugin-anatomy`.

## 6. Show the split, then wait

One table in chat, not a page: Phase · Level · What it adds · Items (**review**) or Components
(**new**, **change**) · Files · Depends on · Evals (kinds; *checkpoint* on the phases that are
one, *mechanical* on the rest; rough tokens for behavioral and trigger rows from the cost table
in `eval-kinds.md`). Under it: phase and level counts, every `E split` warning and what you
did about it, the plan's behavioral total in tokens, and the gap answers you wrote into the
spec. Then one `AskUserQuestion`: approve, or change (the user says what). Revise and re-show
the whole table until approved. Nothing is written before that.

## 7. What is written

All under `site/notes/<slug>/`, from `${CLAUDE_PLUGIN_ROOT}/templates/phases/`. Copy the
headings and fill every one, or delete it with a line saying why. The why, the workflows and
the non-goals stay in the spec; the overview points to it.

| File | Template | Holds |
|---|---|---|
| `<slug>-00-overview.md` | `overview.md` | what changes at a glance; the contents tree; **Files other files parse**; the **Phases** table; **Evals by phase** |
| `<slug>-NN-<name>.md`, one per phase | `phase.md` | the phase's **Decisions**, **Files**, **Specification** anchored on quoted text, Steps, **Evals** copied from the overview, and Done when; written by its planner (§8) |
| `<slug>-progress.md` | `progress.md` | one row per phase: status, commit, eval logs, notes for the next chat |
| `evals/sets/<target>.json` and harness sheets | `run-evals`' set shape | every behavioral row's prompts and expectations; written by the eval writers (§9) |

**The overview carries everything that crosses phases**, because a planner sees one phase and
a builder sees one phase. The **Phases** table (`| Phase | Note | Level | What it adds | Items
| Files | Depends on |`) says what each phase owns: everything not in a Files cell, but for
the shared files, is another phase's. **Files other files parse** names, exactly, every
heading, field or column one phase writes and another reads, with both phases; no note may
rename one. **Evals by phase** holds every row; a note copies its rows and may not loosen a
pass bar, which `P notes-check` compares. Exact paths, exact names, every pass bar, the
commit-message prefix. A sentence starting "consider" or "if appropriate" is a decision not
taken: take it, or ask it as a gap.

## 8. The notes

Written once the overview and ledger are in and `E coverage` and `P plan-check` pass, and
before the eval sets, since a planner may find a gap the sets must know about.

1. **One planner per phase, a level at a time.** For each level in order, spawn one
   general-purpose subagent per phase of the level, all in one message (a level over ten
   phases in two messages), each with the prompt in `references/unit-planner.md`. Wait for
   the whole level. A planner runs `P brief <slug> --phase N`, reads the earlier notes the
   brief names on its files, the component references its items need and the files it owns,
   and writes `site/notes/<slug>/<slug>-NN-<name>.md`: anchors quoted from the files as the
   earlier notes leave them, never line numbers. It settles what the spec left to the phase and returns what is
   the user's as *asked*.
2. **After each level**, `P notes-check <slug>`. A missing note: respawn its planner once
   with the lines naming it. Two notes of one level on one file: a split to redo (an item
   moved, or the file named shared and why).
3. **Then the unify agent**, one general-purpose subagent with the prompt in
   `references/unify.md`. It reads every note's **Decisions**, **Files** and **Specification**
   and the overview's **Files other files parse**, makes names agree where notes meet (a
   module one creates and another imports, a heading one writes and another reads, two rows
   added to one shared table, a helper two notes each invent), edits the notes and that one
   table, runs `notes-check` to `ok`, and returns what it changed and every question,
   deduplicated.
4. **Then the questions, in one round.** Every *asked* and *unresolved* line goes to the user
   in one `AskUserQuestion`, as §3 says. Write each answer into the spec's **Decisions taken**
   with Origin *planning* and into the **Decisions** of the notes that asked. An answer that
   reopens the design stops the plan, as in §3.

## 9. The eval sets

One general-purpose subagent per target with a behavioral row, all in one message, each with
the prompt in `references/eval-writer.md`. A writer reads the spec, the overview's rows for
its target, `eval-kinds.md` and `run-evals`' set shape, and writes that set and its harness
sheets. Then, per set, before committing:

- `python3 ${CLAUDE_PLUGIN_ROOT}/skills/run-evals/scripts/eval_workspace.py validate
  evals/sets/<target>.json` exits 0;
- every id the overview names exists in the set and nothing else was added;
- every expectation is observable in `outputs/` or the transcript, and at least one per new
  eval could fail against the row's baseline;
- a changed target keeps its existing evals, the new ones appended with `added_in: "<slug>
  phase 0, run from phase N"`.

Fix a failing set yourself, or respawn its writer once with the list. A set still wrong after
that is reported in chat, not committed.

## Steps

1. §1 and §2: find the spec, read it and nothing else.
2. §3: ask about every gap in one round. Stop if a design needs reopening.
3. §4 and §5: split (**review**: from `E split`), place the evals, and get the table approved
   per §6. Nothing below runs before that.
4. §7: write the overview, then the ledger: phase 0 `done` or `in progress` per §4, every
   other row `todo`.
5. **review**: `E coverage site/notes/<slug>/<slug>-edits.md site/notes/<slug>/<slug>-00-overview.md`
   prints `ok`; fix Items, Files, Level or Depends on cells until it does. Every plan:
   `P plan-check <slug>` exits 0; a row placed before a phase that touches its target moves to
   the later checkpoint unless that phase only cites the file.
6. §8: the planners, a level at a time, `P notes-check` after each; the unify agent; the
   questions in one round, their answers written into the spec and the notes.
   `P notes-check <slug>` exits 0 at the end.
7. §9: the eval writers, and the checks on what they wrote.
8. If the plugin has a `contracts.yml`, run `check-contracts`. `site/notes/<slug>/` is in its
   scope: an overview or note quoting a forbidden pattern is reworded, or the pattern scoped
   with `files:`. Fix the note, not the claim.
9. One commit: the overview, every note, the eval sets, the ledger, the gap answers in the
   spec, any item split in the edit list. Message: `<plugin> <slug> (phase 0): plan, notes
   and evals for <what>`. Push nothing.
10. Print, for the next chat:

    > Branch `<plugin>-<slug>`. Run `/plugin-dev:run-phase <slug>` from `<plugin>/`, or
    > `/plugin-dev:run-phases <slug>` to run them all from one chat.

    And say how many phases and levels, how many questions were asked and answered, and
    whether the next chat starts with phase 0's platform-fact evals or with phase 1.
