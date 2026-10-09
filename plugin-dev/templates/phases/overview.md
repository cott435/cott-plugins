# <plugin> <slug> — overview

Branch: `<plugin>-<slug>`. Release at the end: `<x.y.z>` — proposed to `bump-version` in
the last phase (a change: a bump; a new plugin: tagging `0.1.0` as scaffolded). Nothing
here bumps or tags anything. Date: <date>.

This is the plan the phases are run from. Each row under **Phases** is one phase, done in
the order listed, one chat and one commit each, by `/plugin-dev:run-phase <slug>`, which
writes the phase's note when the phase starts, from its row here and the files as they are
then. Nothing in a later phase is required by an earlier one, so the branch is mergeable at
any phase boundary.

The why and the decisions are in the spec, approved before this was written:
<`<slug>-design.md` (its workflows, charts and non-goals) and/or `<slug>-edits.md` (its
items, by id)>. This note does not repeat them; it says what the spec turns into, file by
file and phase by phase, and everything one phase needs from another.

<!-- Lines marked (change), (new) or (review) apply to that mode; delete the others. -->

## What changes, at a glance
<!-- (new): retitle "What the plugin is, at a glance" -->

- Agents: <(change) n → m; (new) the list, one line each: role, tools, what it writes>.
- Workflow skills: <(change) n → m with `+`/`~` names; (new) the list in the order a user
  runs them>.
- Knowledge skills: <same>.
- <Scripts, templates, config, `contracts.yml`.>
- Every new skill lands in the files the plugin's `CLAUDE.md` names, in the same commit,
  and its checks run before that commit. <(new) Name those files: this plugin's `CLAUDE.md`
  is written in phase 1 and this line is its first rule.>

## The contents tree

Additions `+`; changed `~`; unmarked is unchanged. <(new) Everything is `+`; the tree is
the plugin as it will be after the last phase.>

```
<plugin>/
├── agents/
│   ├── <name>.md        ~ <one line: what changes>
│   └── <name>.md        + <one line: what it is>
├── skills/
│   └── <name>/          + <kind> <one line>
└── …
```

## Files other files parse

<Every heading, field or column one phase writes and a file in another phase reads, named
exactly. A phase note may not rename anything here; a rename is a Deviation.>

| Path or heading | Written by (phase) | Read by (phase) | Status |
|---|---|---|---|
| | | | new / new heading / changed |

<(new) Every row here is a `contracts.yml` entry some phase writes; its note names which.>

## Phases

One commit per phase. Commit messages begin `<plugin> <slug> (phase N): <what>`. After
every phase that touches an agent or skill: the plugin's own rules, `check-contracts`,
`build-site`, then the phase's evals logged with `log-eval`, then the commit.

<Items: (review) the edit-list ids and ranges the phase lands, `E-001, E-004–E-009`, every
item in exactly one row (`scripts/edits.py coverage` checks it); (new, change) the
components and build-order lines it builds. Must not touch: what a neighbouring phase owns
that this one would be tempted to edit. Depends on: phase numbers, or `all`.>

| Phase | Note | What it adds | Items | Must not touch | Depends on |
|---|---|---|---|---|---|
| 0 | 00-overview | this overview, the eval sets and the ledger; platform-fact evals <IDs> from the spec's assumed facts | — | — | spec |
| 1 | 01-<name> | <(new) the smallest working plugin: one agent or one skill, its README, `CLAUDE.md`, `contracts.yml` with one claim> | | | 0 |
| N | 0N-<name> | end-to-end eval; README, `site/flow.md`, `site/workflows/`, `CHANGELOG.md`; release proposed in chat | | | all |

<Which phases may pair in one chat, and which must not.>

## Evals by phase

<Every phase's eval rows. run-phase copies its phase's rows into its note's Evals and never
loosens a pass bar. Kind is one of run-evals' kinds: mechanical · load · behavioral ·
trigger · platform-fact. A behavioral row names its set file and eval IDs; the prompts are
in that set already.>

| Phase | ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|---|
| 1 | <ID> | <kind> | <skill or agent> | <none / previous / ref> | <evals/sets/x.json 1,2> | <checkable condition> |

## Breaking changes to list in `CHANGELOG.md`

<!-- From the design's **What must not break**; listed here so the last phase finds them. -->
<!-- (new): delete; a first release has none. -->

1. <behavior a user of the plugin will notice, and what to do about it>
