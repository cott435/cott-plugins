# <plugin> <slug> — overview

Branch: `<plugin>-<slug>`. Release at the end: `<x.y.z>` — proposed to `bump-version` in
the last phase (a change: a bump; a new plugin: tagging `0.1.0` as scaffolded). Nothing
here bumps or tags anything. Date: <date>.

This is the index of the phase notes. Each numbered note after this one is one phase, done
in the order listed under **Phases**, one chat and one commit each, by
`/plugin-dev:run-phase <slug>`. Nothing in a later phase is required by an earlier one, so
the branch is mergeable at any phase boundary.

The why, the workflows and their charts, the decisions and the non-goals are in
`<slug>-design.md`, approved before this was written. This note does not repeat them; it says
what the design turns into, file by file and phase by phase.

<!-- Lines marked (change) or (new) apply to that mode; delete the other. -->

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

| Path or heading | Written by | Read by | Status |
|---|---|---|---|
| | | | new / new heading / changed |

<(new) Every row here is a `contracts.yml` entry some phase writes; the phase note names
which.>

## Phases

One commit per phase. Commit messages begin `<plugin> <slug> (phase N): <what>`. After
every phase that touches an agent or skill: the plugin's own rules, `check-contracts`,
`build-site`, then the phase's evals logged with `log-eval`, then the commit.

| Phase | Note | Commit contents | Depends on |
|---|---|---|---|
| 0 | 00 | the phase notes, the eval sets and this ledger; platform-fact evals <IDs> from the design's assumed facts | design |
| 1 | 01 | <(new) the smallest working plugin: one agent or one skill, its README, `CLAUDE.md`, `contracts.yml` with one claim> | 0 |
| N | 0N | end-to-end eval; README, `site/flow.md`, `site/workflows/`, `CHANGELOG.md`; release proposed in chat | all |

<Which phases may pair in one chat, and which must not.>

## Breaking changes to list in `CHANGELOG.md`

<!-- From the design's **What must not break**; listed here so the last phase finds them. -->
<!-- (new): delete; a first release has none. -->

1. <behavior a user of the plugin will notice, and what to do about it>
