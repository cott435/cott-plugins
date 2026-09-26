---
name: design-plugin
description: Turn an idea for a new plugin, or a large change to one, into an approved design through discussion. Interviews the user in rounds, composes the jobs into loops (each loop's unit of work, what makes that unit strong, where its inputs come from, the files where loops meet), shows one flow chart per workflow plus a system chart for approval, then writes the design up for approval. Commits the approved writeup as site/notes/{slug}-design.md, which plan-phases reads in a fresh chat. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json) for a change that touches several agents or skills, or from the marketplace repo root with --new to start a plugin that will have more than a skill or two.
argument-hint: "<slug> [what the change is]  |  --new <plugin-name> [what it does]"
disable-model-invocation: true
---

# Designing a plugin

The design is the only step that needs the whole discussion. Everything after it (the phase
notes, the evals, the phases themselves) should work from a written design and nothing else,
because the discussion that produced it is long, and a model reading all of it plans worse
than one reading its conclusions. So this skill produces one file, the design, and stops.
`plan-phases` reads that file in a fresh chat.

The design is approved in two gates, each shown to the user and revised through discussion
until it is right:

1. **The charts**: one flow chart per workflow and one system chart showing how the workflows
   fit together. These let the user see whether the model has understood the point before
   anything is written up.
2. **The writeup**: the charts plus everything a planner needs, meaning outputs, cost,
   decisions, build order and non-goals.

Nothing is written in the repo before the second gate: no branch, no scaffold, no file.

## Two modes

| | **change** | **new** |
|---|---|---|
| Invoked | inside `<plugin>/` as `design-plugin <slug>` | at the repo root as `design-plugin --new <name>` |
| Slug | as given; usually the target version, `0.5-overhaul` | `0.1`, the first release |
| Branch | `<plugin>-<slug>` from the default branch | `<name>-0.1` from the default branch |
| Charts mark | `new`, `changed`, `removed` against the current bundle | nothing; every component is new |
| Reads first | the plugin's agents, skills, `CLAUDE.md`, `contracts.yml` | the closest existing plugin in this repo, for conventions |
| On approval | writes the design on the branch | invokes `new-plugin` for the scaffold, then writes the design |

Everything below applies to both modes unless it says otherwise.

## Read before asking

A question a file could have answered wastes a round, so reading comes first.

- **change:** read every agent and skill file the change could touch, the plugin's `CLAUDE.md`
  for its own rules, and its `contracts.yml`. Quote heading names, frontmatter fields and
  line-level rules from the files, not from memory.
- **new:** read the most similar plugin in this repo end to end (its README, one agent, one
  workflow skill, one knowledge skill, its `contracts.yml`), so the new one follows the same
  shapes: agents as roles with fixed tools, workflow skills as typed entry points with
  `disable-model-invocation: true`, knowledge skills preloaded by role, nothing stated in two
  files.

## 1. Explore

The request this skill is typed with is a seed, not a spec. "A plugin for X" names a domain,
not the loops, the hand-offs or the boundaries. Expanding it is an interview interleaved with
composing: each round of answers is composed per `references/composing.md`, and what composing
cannot settle becomes the next round.

**A round** is one `AskUserQuestion` call of two to four questions on one theme, each with the
recommended option first and marked *(Recommended)*. Each round is written from the answers to
the ones before it: drop a question the last answer made moot, and ask about a new branch the
last answer opened. Never ask what reading settled, and never ask a question whose every option
leads to the same design.

**Themes, in order.** Skip one only when the request and the reading already settle it.

| # | **new** | **change** |
|---|---|---|
| 1 | Purpose and users: who types the commands, what they have today instead, what one good outcome looks like | What is wrong today: the review, eval or incident behind it, and what must be true after |
| 2 | The workflows: every job, its trigger and deliverable; the source material a practitioner reads one piece at a time, and what a careful reading of one piece looks like | Scope: which agents and skills are in, which are explicitly out |
| 3 | Data, integrations, secrets: sources, APIs, credentials, volumes, where files live | What must not break: headings other files parse, commands users already type, defaults |
| 4 | Boundaries and risk: what it must never do, what needs a human yes, non-goals | Decisions: vendor vs. depend, a default that changes behavior, a name |

After theme 2, compose. `references/composing.md` is the method: find each workflow's unit of
work, make it strong, trace every input the unit needs back to the user, to a file, or to
another loop, and connect the loops at files. Read it in full before composing; the charts draw
exactly what it produces.

**Platform facts.** Verify every Claude Code behavior the design depends on (a frontmatter
field, a substitution, a spawn form) against the Claude Code docs. A fact the docs do not
settle is not assumed. It is written into the design as an assumption, with the answer you
expect, and becomes a phase-0 eval that `plan-phases` schedules before anything depends on it.

**The exploration is done** when composing's checklist ("Before the charts are drawn") holds
and everything still open is either a decision to ask about or a platform fact. Two rounds is
typical for a change and three or four for a new plugin. A fifth means the idea should be split
into two designs.

## 2. The charts, then wait

Draw one chart per workflow and one system chart, with the components table below them, per
`references/charts.md`. In the same order, the page holds:

1. The idea restated: one paragraph, in the user's terms, of what will exist when this is
   built.
2. The system chart.
3. Each workflow's chart with its three-line caption (Unit, Strengthened by, Inputs from).
4. The components table.
5. The suggestions: each with one line of why.

In chat, give the link and a few sentences on the shape: the loops, what feeds what, and which
files are shared. Then ask with one `AskUserQuestion`: approve the charts; change something (the
user says what); and, when there are suggestions, one multi-select question listing them so
each is accepted or rejected by name.

A change means a discussion, as long as it needs to be, then the whole page republished at the
same path and asked again. Only an approval moves on to the writeup, and after approval the
charts change only if the writeup discussion reopens them. Accepted suggestions lose their
dashed styling; rejected ones are deleted and remembered for **Non-goals**.

## 3. The writeup, then wait

Draft the writeup from `${CLAUDE_PLUGIN_ROOT}/templates/phases/design.md` in the session
scratchpad. It is for a reader who was not in this conversation: `plan-phases` reads it to
write every phase note and eval, and `run-phase` reads it for the why. Anything decided here
and not written down is lost. Its sections, in this order:

1. **The idea**: the restated idea, as approved.
2. **Workflows**: per workflow, its approved chart, trigger and deliverable, its unit, what
   strengthens the unit, and an Input · Supplied by table covering every input.
3. **How they fit together**: the system chart, and a File · Written by · Read by · Fields read ·
   Stale when table covering every file two loops meet at.
4. **Components**: the approved components table.
5. **Outputs**: for every file a reader depends on, its sections, what it cites, what it must
   never claim, and when it goes stale.
6. **Cost**: per workflow, what a cold run reads, what a warm run reads, and the horizon each
   assumes.
7. **Decisions taken**: every decision from the discussion, as Decision · Chosen · Alternatives ·
   Why · Origin (*asked*, or *suggested* and accepted).
8. **Platform facts**: every fact the design depends on, each either *verified* (with the doc
   it was checked against) or *assumed* (with the expected answer). An assumed fact becomes a
   phase-0 eval.
9. **Build order**: which components depend on which, and the smallest slice that works end to
   end. This is not the phases; `plan-phases` splits those from it.
10. **What must not break**: change mode only. Headings other files parse, commands users
    already type, defaults, and every breaking change a user will notice. In new mode, delete
    the section.
11. **Non-goals**: what this deliberately does not do, and each declined suggestion as one line.

Write every section or delete it with a line saying why. A sentence that starts "consider" or
"if appropriate" is a decision not taken: take it, or ask it.

Show it the way the charts were shown: republish the same page, now carrying the writeup's
sections as they will read in the file, give the link, and ask with one `AskUserQuestion`:
approve the writeup, or change something. Revise and re-show until it is approved.

## 4. Commit the design

Only after the writeup is approved:

1. Create the branch from the default branch: `<plugin>-<slug>` (**new**: `<name>-0.1`). Put it
   where the repo's `CLAUDE.md` says branch work goes. In this marketplace that is a worktree:
   `git worktree add ../cott-plugins-worktrees/<plugin>_<branch> -b <branch> <default branch>`.
   Work from there.
2. **new only:** invoke `new-plugin` and complete its scaffold and marketplace steps, so the
   design lands in a directory that already builds.
3. Write the approved writeup to `<plugin>/site/notes/<slug>-design.md`, exactly as approved.
4. If the plugin has a `contracts.yml`, run `check-contracts`. `site/notes/` is in its scope, so
   a design that quotes a forbidden pattern must reword it. Fix the design, not the claim.
5. Commit the design (**new**: and the scaffold and marketplace row): `<plugin> <slug>
   (design): <what>`. This is the only commit this skill makes, and it pushes nothing.
6. Print, for the user to start the next chat with:

   > In a new chat, from `<worktree>/<plugin>`: `/plugin-dev:plan-phases <slug>`

   Say why it is a new chat: the planner should see the design and nothing of the discussion,
   so a gap in the design shows up as a question rather than being filled from memory.
