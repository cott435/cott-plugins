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
| 2 | The workflows — every job the user wants done, the steps of each, and what each step hands the next; for each, the source material a practitioner would read, one piece at a time, and how deep "done well" goes | Scope — which agents and skills are in, which are explicitly out |
| 3 | Data, integrations, secrets — sources, APIs, credentials, where files live | What must not break — headings other files parse, commands users already type, defaults |
| 4 | Boundaries and risk — what it must never do, what needs a human yes, non-goals | Decisions — vendor vs. depend, a default that changes behavior, a name |

**Suggestions.** Expanding the idea includes proposing what the user did not ask for but the
design needs: an agent that owns a responsibility nobody else does, a knowledge skill two
agents would otherwise each carry, a safeguard a risky step lacks (a trading plugin with no
risk check, a writer with no reviewer). Each suggestion is named with one line of why and
carried into the proposal marked as a suggestion; it is the user's to accept, never
silently folded in. A suggestion attaches to the design and never carries it: no
component the user asked for reads a suggestion's file, and no phase of the core depends
on a suggestion's phase — so rejecting any one of them removes that component and nothing
else has to be redesigned.

**The interview is done** when the jobs, their source material and their boundaries are
known — enough to compose them, per the next section — and everything still open is either
a decision (ask it) or a platform fact. Verify platform facts the design
depends on (a frontmatter field, a substitution, a spawn form) against the Claude Code
docs; a fact the docs do not settle is not assumed: it becomes a **phase-0 eval** with the
assumed answer written down, and nothing in a later phase depends on it before that eval is
logged. Two rounds is typical for a change, three or four for a new plugin; a fifth means
the idea should be split into two plans.

## Compose the workflows

The interview gives you jobs — the things the user will type. The easy design gives each job
its own command and its own agent: three jobs, three agents, each researching from scratch.
That design is shallow in every job (no agent can go deep when it must also do everything
else), repeats the same research in each, and has nothing to run in parallel. It mirrors
the user's list back to them instead of expanding it, and it is the failure this section
exists to prevent.

Design from the work instead of from the commands:

1. **Find the unit of work.** For each job, ask what a practitioner in the domain actually
   reads or judges one piece at a time — one filing, one paper, one support ticket, one
   source file. That unit is where depth lives, and it is the natural grain for an agent
   that can be run many times in parallel, one instance per unit.
2. **Line the jobs up and find what they share.** Two jobs that each need "the current
   state of this company" or "what this paper found" should not each derive it; that
   understanding is a layer, built once, written to a file, and read by both. Most
   multi-job plugins resolve into some of these layers, bottom to top:
   - **extract** — one agent per unit, fanned out in parallel, each writing one structured
     file;
   - **synthesize** — one agent per entity (a company, a topic, an account) reading every
     unit file for it in order and writing the entity's status — the file everything above
     reads;
   - **compare** — the entity against its peers or baseline (sector and industry, the rest
     of the field, the customer cohort, last period). This layer is core, not a suggestion:
     a professional's judgment is always relative — a margin is good or bad against the
     industry's, a result is new or not against the field — and a design without it hands
     the user conclusions nobody in the domain would sign;
   - **act** — the typed jobs, now thin: each composes the layers below with whatever only
     it needs (today's news, the user's own list) and answers its question.

   Extract, synthesize and act appear when the jobs need them; when one is absent, say why
   in the proposal. Compare is left out only when the entity genuinely has no peer set or
   baseline, and the proposal says so.
3. **Agents are methods, workflow skills are orchestrations.** An agent is one way of
   working, done expertly; if two jobs need the same method they share the agent. A
   workflow skill decides which layers to build or refresh, in what order, and how wide to
   fan out. So the count of agents and the count of commands are unrelated, and a 1:1
   match between them is a sign the composing has not been done yet.
4. **Freshness makes reuse pay.** Each layer's file records what it was built from and
   when, so a job rebuilds a layer only when its inputs changed — a new filing, a new
   paper. That is what makes a screen across thirty entities affordable.
5. **Ask what a practitioner would miss.** Walk the design as the domain's professional
   would and name what they would insist on that no component does — the critic that
   checks a synthesis against its sources, the risk check before a recommendation. Those
   become suggestions.
6. **Size it.** For each job, work out what its first run reads (how many units, how far
   back) and what a warm run reads once the layers exist — a screen of thirty tickers that
   must first read two years of filings for each is a different product from one that
   reads the latest filing. Default every horizon to the least the job's question needs,
   not the most the source offers; a longer one is the user's call. Spend depth where the
   judgment is made: a screen can rank thirty entities on their status files and run the
   peer comparison only on its shortlist, and a pass that only counts, filters or dedupes
   is a script, not an agent.
7. **Say what each output must say.** For every file a reader depends on — a unit note, a
   status file, a job's report — name its sections and the domain rules that make it
   trustworthy: what it must cite, what it must never claim (a suggested reply never
   promises a refund; a thesis never states a price target as fact), and when it goes
   stale. Structure without these rules produces well-organized files nobody can rely on.

Before proposing, check the design against this: which file does more than one job read?
Where does it fan out, and over what? Which layer compares, and against what? If the answer
to any is "none", either fix the design or say in the proposal why this plugin does not
need it. Then remove every suggestion in your head and check the core still works end to
end. Last, read the proposal against itself: the restated idea, the decisions and the cost
table describe the same depth (a paper is not "read in full" in one section and "skimmed"
in another), and every fan-out's arithmetic adds up — batch size × batches covers the
units. If composing surfaces a question only the user can answer — how many entities a
screen covers, how far back the history goes — ask it as one more round.

## Propose, then wait

The proposal is a page the user looks at, not code they have to render in their head. When
the session has the `Artifact` tool, publish the proposal as an Artifact — an HTML page,
following that tool's own rules, with the chart in a `<pre class="mermaid">` block and
the sections below as the page. It must also read correctly as a plain file: open it with
`<meta charset="utf-8">` (the Artifact viewer adds one, a downloaded file has none, and every
dash turns to mojibake), and have it load mermaid itself —
`<script src="https://cdnjs.cloudflare.com/ajax/libs/mermaid/11.15.0/mermaid.min.js"></script>`
at the end of the body, followed by an initializer that matches the viewer's theme and
keeps the chart at full size:

```html
<script>
const t = document.documentElement.dataset.theme;
const dark = t ? t === "dark" : matchMedia("(prefers-color-scheme: dark)").matches;
mermaid.initialize({startOnLoad: true, theme: dark ? "dark" : "default",
                    flowchart: {useMaxWidth: false}});
</script>
```

with the `<pre class="mermaid">` inside a container styled `overflow-x: auto`. The chart
then renders the same when the file is downloaded or opened locally, not only inside the
Artifact viewer, and a wide chart scrolls instead of shrinking its text to nothing. Republish the same file path after
every revision so the link stays the same. In chat, give the link and a short summary of
the design — the layers and what is shared — then ask. Without the `Artifact` tool, use
whatever tool the session has for showing a rendered diagram; only when there is none,
put the `mermaid` block in chat. Either way nothing in the repo — no branch, no scaffold,
no file — exists before the user approves. The proposal holds, in this order:

1. **The idea, restated** — one paragraph, in the user's terms, of what will exist after the
   last phase.
2. **The flow chart** — a `mermaid` `flowchart TB` of how the work moves: each typed
   command → the agents it spawns, with fan-out shown as such (`filing-reader ×N`) → the
   files they write → whoever reads each file next. It is for seeing the shape at a glance,
   so it must read at page width without scrolling far: aim for at most about 20 nodes and
   30 edges. A chart past that is a wiring diagram nobody reads — the first trial run drew
   31 nodes and 55 edges and came out nearly four thousand pixels wide. To stay inside it:
   - one node per typed command and per agent, each exactly once (an agent with two modes
     is one node with its edges labelled by mode);
   - one node per shared file, and one per layer for the per-unit files (`notes/*.md`),
     not one per job's report — a report nobody else reads can be the command's edge label;
   - knowledge skills and scripts go in the components table, not the chart; an agent's
     preloaded skills can be a second line in its label. Dotted preload edges from one
     skill to five agents are five edges that say nothing about the flow;
   - one `subgraph` per layer (extract, synthesize, compare, act), not per command, so the
     chart shows what the commands share; keep edge labels to a word or two, since long
     labels are what widen a chart most.

   Suggestions are dashed (`classDef suggested stroke-dasharray:5 5`). In **change** mode,
   nodes carry `classDef new`, `changed` or are left unmarked, and a node that is removed is
   shown struck with `classDef removed`. Nothing appears in the chart that is not in the
   table below.
3. **The components** — one table: Name · Kind (agent, workflow skill, knowledge skill,
   script) · Layer · Role · Reads · Writes · Used by (the jobs that depend on it) · Origin:
   *asked* (an answer names it), *composed* (the layers need it to serve what was asked —
   extract, synthesize, compare), or *suggested: <why>* (optional; the user accepts or
   rejects it). Label honestly: a component nobody asked for is not *asked*.
4. **The outputs** — for each file a reader depends on, its sections and its rules: what it
   cites, what it must never claim, when it goes stale.
5. **Cost** — for each job, what a first run reads and what a warm run reads, and the
   horizon each assumes.
6. **Decisions taken** — every answer from the interview that is a decision, with the
   alternatives it beat.
7. **The phases** — one line each: number, what it adds, what it depends on; which may
   pair. Suggestions get their own phases or are named as optional additions to one, and
   the line says what disappears if the suggestion is rejected; and, per phase, its eval
   budget — which kinds it runs and, for behavioral and trigger evals, roughly how many
   tokens, from the cost table in `run-evals`' eval kinds.
8. **Non-goals** — what this deliberately does not do.

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

### The phase note

Its sections, in order:

- **`# NN — <name>`**, then a purpose paragraph: what the phase adds and the gap it closes,
  written for a chat that has read only the overview, the ledger and this note.
- **`## Decisions`** — anything settled here rather than in the overview, each with its
  reason.
- **`## Files`** — a Path · Change table, one row per file the phase touches.
- **`## Specification`** — the exact content: frontmatter, heading names, rules,
  `contracts.yml` entries, and any prompt another model will be given, verbatim.
- **`## Steps`** — ordered so the bundle is consistent after each one.
- **`## Evals`** — the table described under **Rules for the split**.
- **`## Done when`** — conditions checkable without judgment.
- **`## Deviations`** — appended by `run-phase` when the note could not be followed as
  written; this skill never writes it.

`references/example-phase.md` walks through a real one.

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
  hand-offs work goes before the things that rely on it. In a layered design that means
  bottom-up — the extract agent and its file format before the synthesis that reads them,
  the shared layers before the jobs that compose them — with the thinnest job that uses a
  layer shipped in the same phase, so every phase ends with something a user can type. The
  phases table names each phase's dependencies explicitly.
- **Phase 0 is the design set** — this skill's commit — plus platform-fact evals. In **new**
  mode it is also the scaffold: invoke `new-plugin` and do exactly its steps (directory,
  templates, `plugin.json`, the marketplace row) before writing the notes, so the notes
  live in a directory that already builds.
- **The last phase is always** the end-to-end eval, the docs (`README.md`, `site/flow.md`,
  `site/workflows/`, `CHANGELOG.md`'s unreleased section), and the release *proposal* —
  which `bump-version` decides on a yes; never this skill or `run-phase`.
- **Every phase has an `## Evals` table**: `| ID | Kind | Target | Baseline | Set evals |
  Pass bar |`.
  - Kind is one of `run-evals`' kinds — `mechanical`, `load`, `behavioral`, `trigger`,
    `platform-fact` — whose methods are in `run-evals/references/eval-kinds.md`; read it
    before choosing.
  - A behavioral row names `evals/sets/<target>.json` and eval IDs; the prompts and
    expectations are written into that set in the phase-0 commit, with a harness sheet under
    `evals/sets/files/<target>/` for any target that asks the user something. A new target
    gets a new set; a changed one gets evals appended with `added_in: "<slug> phase 0, run
    from phase N"`. Trigger sets are the exception: the phase that adds a model-invoked
    skill writes its `<target>.trigger.json`, since it needs the final description.
  - A phase that changes a target with an existing set reruns that set as regression, as
    its own row.
  - The pass bar is checkable without judgment (default: every expectation passes and the
    target's pass rate ≥ the baseline's).
- **Every phase touching an agent or skill** runs the plugin's own rules, `check-contracts`
  (once a `contracts.yml` exists — in **new** mode, phase 1 creates it with the first claim
  the README makes about the bundle), and `build-site`, then its Evals table through
  `run-evals`.

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
   platform facts it depends on. Compose the jobs into layers, per **Compose the
   workflows**.
3. Publish the proposal and ask for approval, per **Propose, then wait**. Revise and re-show
   until approved. Nothing below runs before that.
4. From the default branch: `git checkout -b <plugin>-<slug>` (**new**: `<name>-0.1`).
5. **new only:** invoke `new-plugin` and complete its scaffold and marketplace steps. Do not
   push; the phases will.
6. Write the overview from the approved proposal, then one note per phase, then the eval
   sets and harness sheets the notes' behavioral rows name, then the ledger with phase 0
   `in progress` and every other row `todo`.
7. If the plugin has a `contracts.yml`, run `check-contracts` — `site/notes/` is in its
   scope, so a note that quotes a forbidden pattern must scope the pattern with `files:` or
   be reworded. Fix the note, not the claim.
8. Commit the notes, the eval sets and the ledger (**new**: and the scaffold and
   marketplace row): `<plugin> <slug> (phase 0): design set for <what>`. This is the only commit this skill
   makes; it pushes nothing.
9. Print, for the user to paste into the next chat:

   > Branch `<plugin>-<slug>`. Run `/plugin-dev:run-phase <slug>` from `<plugin>/`.

   And say how many phases there are, which may pair in one chat, and that phase 0's evals
   (if any) are the first thing `run-phase` will do.
