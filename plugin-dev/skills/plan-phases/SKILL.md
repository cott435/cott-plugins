---
name: plan-phases
description: Expand a plugin's large change - or a whole new plugin - from a one-line idea into an approved design, then split it into phases, each sized for one Claude Code chat. Interviews the user in rounds, proposes a flow chart of every skill and agent with suggested additions marked, waits for approval, and only then writes a branch, an overview note, one note per phase with its own evals, and a progress ledger that run-phase reads. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json) for a change that touches several agents or skills, or from the marketplace repo root with --new to start a plugin that will have more than a skill or two.
argument-hint: "<slug> [what the change is]  |  --new <plugin-name> [what it does]"
disable-model-invocation: true
---

# Planning in phases

A change that touches several agents or skills, or a plugin built from nothing, does not
fit one conversation: the context fills before the evals run, and the second half of the
work is done by a model that has forgotten the first. So the work is split into phases,
each small enough for one chat, and the split is written down before any of it starts — in
notes a fresh chat can read cold, and a ledger that says which phase is next.

The split is only as good as the design it splits, and a design written from a one-line
request is a guess. So before anything is written, this skill expands the idea with the
user — an interview in rounds, then a proposal with a flow chart of every skill and agent —
and writes nothing until the user approves it.

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

## Read before asking

A question a file could have answered wastes a round, so reading comes first:

- **change:** read every agent and skill file the change could touch, the plugin's
  `CLAUDE.md` for its own rules — a three-file rule, a contracts file — and its
  `contracts.yml`. Quote heading names, frontmatter fields and line-level rules from the
  files, not from memory.
- **new:** read the most similar plugin in this repo end to end (its README, one agent, one
  workflow skill, one knowledge skill, its `contracts.yml`) so the new one follows the same
  shapes: agents as roles with fixed tools, workflow skills as typed entry points with
  `disable-model-invocation: true`, knowledge skills preloaded by role, nothing stated in
  two files.

## Expand the idea

The request this skill is typed with is a seed, not a spec — "a plugin for a stock trading
agent" names a domain, not the agents, the hand-offs or the boundaries. Before anything is
proposed, the idea is expanded in an interview, in rounds.

**A round** is one `AskUserQuestion` call of two to four questions on one theme, each with
the recommended option first and marked *(Recommended)*. Each round is written from the
answers to the ones before it: a question the last answer made moot is dropped, a new
branch the last answer opened is asked about. Never ask what reading settled, and never ask
a question whose every option leads to the same design.

**Themes, in order** — skip one only when the request and the reading already settle it:

| # | **new** | **change** |
|---|---|---|
| 1 | Purpose and users — who types the commands, what they have today instead, what one good outcome looks like | What is wrong today — the review, eval or incident behind it, and what must be true after |
| 2 | The workflow — the steps a user takes in order, which are typed, which run on their own, what each step hands the next | Scope — which agents and skills are in, which are explicitly out |
| 3 | Data, integrations, secrets — sources, APIs, credentials, where files live | What must not break — headings other files parse, commands users already type, defaults |
| 4 | Boundaries and risk — what it must never do, what needs a human yes, non-goals | Decisions — vendor vs. depend, a default that changes behavior, a name |

**Suggestions.** Expanding the idea includes proposing what the user did not ask for but the
design needs: an agent that owns a responsibility nobody else does, a knowledge skill two
agents would otherwise each carry, a safeguard a risky step lacks (a trading plugin with no
risk check, a writer with no reviewer). Each suggestion is named with one line of why and
carried into the proposal marked as a suggestion; it is the user's to accept, never
silently folded in.

**The interview is done** when every component the proposal will show can be named with
its role, what it reads, what it writes, and which answer it serves — and everything still
open is either a decision (ask it) or a platform fact. Verify platform facts the design
depends on (a frontmatter field, a substitution, a spawn form) against the Claude Code
docs; a fact the docs do not settle is not assumed: it becomes a **phase-0 eval** with the
assumed answer written down, and nothing in a later phase depends on it before that eval is
logged. Two rounds is typical for a change, three or four for a new plugin; a fifth means
the idea should be split into two plans.

## Propose, then wait

The proposal is shown in chat, in this order, and nothing — no branch, no scaffold, no
file — exists before the user approves it:

1. **The idea, restated** — one paragraph, in the user's terms, of what will exist after the
   last phase.
2. **The flow chart** — a `mermaid` `flowchart` of every component and how they connect:
   each typed command → the skill it runs → the agent it spawns → the file that agent
   writes → whoever reads that file next; knowledge skills as dotted links into the agents
   that preload them; scripts beside the skill that runs them. Suggestions are dashed
   (`classDef suggested stroke-dasharray:5 5`). In **change** mode, nodes carry
   `classDef new`, `changed` or are left unmarked, and a node that is removed is shown
   struck with `classDef removed`. Every component in the table below appears in the chart
   exactly once — an agent with two modes is one node with its edges labelled by mode — and
   nothing appears in the chart that is not in the table. Past about thirty nodes, put each
   typed command's path in its own `subgraph` so the chart still reads top to bottom.
3. **The components** — one table: Name · Kind (agent, workflow skill, knowledge skill,
   script) · Role · Reads · Writes · Origin (*asked* or *suggested: <why>*).
4. **Decisions taken** — every answer from the interview that is a decision, with the
   alternatives it beat.
5. **The phases** — one line each: number, what it adds, what it depends on; which may
   pair.
6. **Non-goals** — what this deliberately does not do.

Then one `AskUserQuestion`: approve as shown; approve with changes (the user says which);
and, when there are suggestions, one multi-select question listing them so each is
accepted or rejected by name. A change means the whole proposal is shown again — not a
diff — and asked again. Only an approval moves on to **Steps** 4 onward.

What was approved is what gets written: the chart becomes the overview's **The flow**
as shown (suggestion styling removed from accepted ones, rejected ones deleted), the
components become **What changes, at a glance** and the contents tree, the decisions
become **Decisions taken**, the phase lines become the **Phases** table, and each rejected
suggestion is a line under **Non-goals** saying it was considered and declined.

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
in the interview.

## Steps

1. Read, per **Read before asking**.
2. Interview in rounds until the idea is expanded, per **Expand the idea**; verify the
   platform facts it depends on.
3. Show the proposal and ask for approval, per **Propose, then wait**. Revise and re-show
   until approved. Nothing below runs before that.
4. From the default branch: `git checkout -b <plugin>-<slug>` (**new**: `<name>-0.1`).
5. **new only:** invoke `new-plugin` and complete its scaffold and marketplace steps. Do not
   push; the phases will.
6. Write the overview from the approved proposal, then one note per phase, then the ledger
   with phase 0 `in progress` and every other row `todo`.
7. If the plugin has a `contracts.yml`, run `check-contracts` — `site/notes/` is in its
   scope, so a note that quotes a forbidden pattern must scope the pattern with `files:` or
   be reworded. Fix the note, not the claim.
8. Commit the notes and the ledger (**new**: and the scaffold and marketplace row):
   `<plugin> <slug> (phase 0): design set for <what>`. This is the only commit this skill
   makes; it pushes nothing.
9. Print, for the user to paste into the next chat:

   > Branch `<plugin>-<slug>`. Run `/plugin-dev:run-phase <slug>` from `<plugin>/`.

   And say how many phases there are, which may pair in one chat, and that phase 0's evals
   (if any) are the first thing `run-phase` will do.
