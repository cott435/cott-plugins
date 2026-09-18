---
name: plan-phases
description: Split a plugin's large change - or a whole new plugin - into phases, each sized for one Claude Code chat, and write them down before any work starts - a branch, an overview note, one note per phase with its own evals, and a progress ledger that run-phase reads. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json) for a change that touches several agents or skills, or from the marketplace repo root with --new to start a plugin that will have more than a skill or two.
argument-hint: "<slug> [what the change is]  |  --new <plugin-name> [what it does]"
disable-model-invocation: true
---

# Planning in phases

A change that touches several agents or skills, or a plugin built from nothing, does not
fit one conversation: the context fills before the evals run, and the second half of the
work is done by a model that has forgotten the first. So the work is split into phases,
each small enough for one chat, and the split is written down before any of it starts — in
notes a fresh chat can read cold, and a ledger that says which phase is next.

This skill writes the notes, the ledger and the branch. `run-phase` does the phases, one
per chat. Both are typed by the user; neither pushes.

## Two modes

| | **change** | **new** |
|---|---|---|
| Invoked | inside `<plugin>/` as `plan-phases <slug>` | at the repo root as `plan-phases --new <name>` |
| Slug | as given; usually the target version, `0.5-overhaul` | `0.1` — the first release |
| Branch | `<plugin>-<slug>` from the default branch | `<name>-0.1` from the default branch |
| Phase 0 | the design set; platform-fact evals | `new-plugin`'s scaffold and marketplace row, then the design set |
| Overview says | what changes, marked `+`/`~` against the current bundle | what the plugin is; every tree item is `+` |
| Last phase proposes | a bump at the level the breaking list implies | tagging `0.1.0` as scaffolded — the first release |
| Reads first | the plugin's agents, skills, `CLAUDE.md`, `contracts.yml` | the brief the user gives; the closest existing plugin in this repo, for conventions |

Everything below applies to both unless it says otherwise.

## Ask first, if it is not already clear

- **change:** the slug; the items in scope, as a list — each becomes one phase or a pair.
- **new:** the name (kebab-case: directory and `/<name>:` prefix); one line on what it does;
  whether it has agents, commands, or only skills; and what it is *for* in enough detail to
  name its agents and skills — a plugin whose purpose is one sentence gets one phase per
  sentence of purpose, which is the wrong split.
- Either: anything that is a **decision of the user's**, not a fact — vendor vs. depend on
  another plugin, a default that changes behavior, a name. Ask once, recommended option
  first, and record the answer under **Decisions taken** in the overview.

## Research before writing

The notes must leave nothing for the next chat to guess, so what they claim is checked now:

- **change:** read every agent and skill file the change touches. Quote heading names,
  frontmatter fields and line-level rules from the files, not from memory. Read the plugin's
  `CLAUDE.md` for its own rules — a three-file rule, a contracts file — so every phase's
  steps include them.
- **new:** read the most similar plugin in this repo end to end (its README, one agent, one
  workflow skill, one knowledge skill, its `contracts.yml`) so the new one follows the same
  shapes: agents as roles with fixed tools, workflow skills as typed entry points with
  `disable-model-invocation: true`, knowledge skills preloaded by role, nothing stated in
  two files.
- Both: verify platform facts the design depends on (a frontmatter field, a substitution,
  a spawn form) against the Claude Code docs. A fact the docs do not settle is not assumed:
  it becomes a **phase-0 eval** with the assumed answer written down, and nothing in a later
  phase depends on it before that eval is logged.

## What is written

All under `<plugin>/site/notes/`, so the site builder renders them under Notes:

| File | From template | Holds |
|---|---|---|
| `<slug>-00-overview.md` | `templates/phases/overview.md` | why; decisions taken; what changes (or what the plugin is); the contents tree; the flow; files other files parse; the phases table with dependencies; breaking changes (change mode); non-goals |
| `<slug>-NN-<name>.md`, one per phase from `01` | `templates/phases/phase.md` | purpose; decisions; files touched; the exact specification; steps; evals; done-when |
| `<slug>-progress.md` | `templates/phases/progress.md` | one row per phase: status, commit, eval logs, notes for the next chat |

Templates are at `${CLAUDE_PLUGIN_ROOT}/templates/phases/`. Copy the headings; fill every
one or delete it with a line saying why.

## Rules for the split

- **A phase is mergeable on its own.** The branch is releasable at every boundary: no phase
  leaves an agent citing a heading nobody writes yet. A skill that needs a later phase's
  file is created in that later phase, not stubbed. In **new** mode this means phase 1 is
  the smallest thing that is a working plugin — one agent, or one skill, plus the README
  that describes only what exists — and every later phase adds to a bundle that already
  loads and builds.
- **A phase fits one chat.** Heuristic: one concept; at most six or so files edited; at most
  one new agent or two new skills. Two independent small items may pair; nothing else does.
- **Ordered by dependency**, foundations first — whatever changes how commits, status or
  hand-offs work goes before the things that rely on it. The phases table names each
  phase's dependencies explicitly.
- **Phase 0 is the design set** — this skill's commit — plus platform-fact evals. In **new**
  mode it is also the scaffold: invoke `new-plugin` and do exactly its steps (directory,
  templates, `plugin.json`, the marketplace row) before writing the notes, so the notes
  live in a directory that already builds.
- **The last phase is always** the end-to-end eval, the docs (`README.md`, `site/flow.md`,
  `site/workflows/`, `CHANGELOG.md`'s unreleased section), and the release *proposal* —
  which `bump-version` decides on a yes; never this skill or `run-phase`.
- **Every phase has at least one eval**, named in its note by ID and kind (mechanical or
  behavioral) with its pass condition. Behavioral evals run against one fixture that an
  early phase creates under `evals/fixtures/`, so results compare across phases.
- **Every phase touching an agent or skill** runs the plugin's own rules, `check-contracts`
  (once a `contracts.yml` exists — in **new** mode, phase 1 creates it with the first claim
  the README makes about the bundle), and `build-site`, before its evals.

## No ambiguity

Each phase note is written for a model that has read only the overview, the ledger and
that note. So it carries: exact file paths; exact frontmatter blocks for new agents and
skills; exact heading and column names for anything another file parses; the
`contracts.yml` entries that will enforce them; the eval and its pass condition; the commit
message; and a **Done when** a reader can check without judgment. A sentence that starts
"consider" or "if appropriate" is a decision not taken — take it, or make it a question
under **Ask first**.

## Steps

1. Ask what needs asking; research per above.
2. From the default branch: `git checkout -b <plugin>-<slug>` (**new**: `<name>-0.1`).
3. **new only:** invoke `new-plugin` and complete its scaffold and marketplace steps. Do not
   push; the phases will.
4. Write the overview, then one note per phase, then the ledger with phase 0
   `in progress` and every other row `todo`.
5. If the plugin has a `contracts.yml`, run `check-contracts` — `site/notes/` is in its
   scope, so a note that quotes a forbidden pattern must scope the pattern with `files:` or
   be reworded. Fix the note, not the claim.
6. Commit the notes and the ledger (**new**: and the scaffold and marketplace row):
   `<plugin> <slug> (phase 0): design set for <what>`. This is the only commit this skill
   makes; it pushes nothing.
7. Print, for the user to paste into the next chat:

   > Branch `<plugin>-<slug>`. Run `/plugin-dev:run-phase <slug>` from `<plugin>/`.

   And say how many phases there are, which may pair in one chat, and that phase 0's evals
   (if any) are the first thing `run-phase` will do.
