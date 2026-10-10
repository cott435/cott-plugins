---
name: revise-plugin
description: Plan a change across a whole existing plugin from facts about it - audited issues, eval results, contradictions, a context budget, a rule every agent and skill must now meet - agent by agent and skill by skill, whatever workflow each belongs to. Agrees the goal and the units with you, runs waves of parallel unit agents that each read one role or one set of scripts whole and write findings, then one reconcile agent that turns every finding into one deduplicated edit list, site/notes/{slug}/{slug}-edits.md, asks the decisions the findings leave open, and commits the list on a worktree branch for plan-phases to plan in a fresh chat. Use inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json) for a change that touches many agents and skills; not for a new plugin or a new or redrawn workflow (design-plugin), and not for a few audited issues (fix-issues).
argument-hint: "<slug> [what the change is for | issues <selection>]"
disable-model-invocation: true
---

# Revising a plugin

A change to a plugin reaches `plan-phases` by one of two routes, and which one depends on
where the change starts and what it is organized by.

- **From an idea, by workflow.** A new plugin, a workflow added or redrawn. What should
  exist has to be worked out with you, one workflow at a time: its driver, its agents, its
  ledger. That is `design-plugin`, and its spec is a design.
- **From facts, by agent and skill.** The plugin exists, and something known about it says
  it must change in many places at once: issues an audit keeps filing, eval results,
  prompts that contradict each other, a context budget gone too far, or a rule every agent
  and skill must now meet (`plugin-anatomy`'s driver shape, a new platform fact). No
  workflow is being invented. The work is finding every place the facts apply, in a bundle
  too large for one chat to read, and the decisions are few and narrow. That is this skill,
  and its spec is an edit list.

It agrees the goal with you, reads the plugin as waves of agents that each take one role or
one set of scripts whole, and reconciles their findings into one edit list: every item with
its files and lines, its mechanism, its dependencies and the evals that prove it. That list
is the spec. `plan-phases` splits it into phases in a fresh chat, the way it splits a design.

The reading is a review, and the files it leaves keep that name (`<slug>-review-plan.md`,
`templates/review/`, `Mode: review`), as plans already in flight have them. The review is the
means. What this skill is for is the change.

This chat orchestrates and nothing else. It reads the plugin's shape (frontmatter, line
counts, the audit index), never the bodies of its files, and it reads the findings and the
edit list only through `scripts/edits.py`. The units do the reading, so this chat stays small
however big the plugin is.

`E` below is `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/edits.py`.

| | `design-plugin` | `revise-plugin` | `fix-issues` |
|---|---|---|---|
| Starts from | an idea for what should exist | facts about the plugin as it is | issues an audit already filed |
| Organized by | workflow: one driver and its loop at a time | agent and skill, across every workflow | issue |
| Size | a new plugin, or one workflow | many agents and skills | a few issues: `issues.py route` exits 0 |
| The spec | the design: charts and a writeup | the edit list, item by item | one planned edit per issue |
| Then | `plan-phases` | `plan-phases` | edits in the same chat |

`fix-issues` is the small end of this route: it stops and names this skill when
`issues.py route` gives its selection here (more than six issues, more than three issues
across more than three roles, or an issue that recurred after two fixes).

## Setup

1. Confirm this is a plugin subdirectory (`.claude-plugin/plugin.json` exists). Its `name` is
   **P**. With no slug argument, stop and ask for one.
2. The branch is `<P>-<slug>`. Put it where the repo's `CLAUDE.md` says branch work goes; in
   this marketplace that is a worktree:
   `git worktree add ../cott-plugins-worktrees/<P>_<slug> -b <P>-<slug> <default branch>`.
   If the branch and its worktree exist, work there. Never switch the user's own checkout.
   Every path below is in the worktree.
3. The plan's folder is `<P>/site/notes/<slug>/`. If `<slug>-edits.md` is already there, say
   so and stop: the edit list is written, and the next step is `plan-phases`.
4. When the argument says `issues` and a selection, as `fix-issues` and `audit-run` print
   it, resolve it once with `python3 ${CLAUDE_PLUGIN_ROOT}/scripts/issues.py list` (the
   ids as given; `--session <id8>` for `run:<id8>`; `--status open,recurred` for `open`;
   `--status recurred`). Its lines (id, status, severity, fault, the roles each issue
   applies to, title) are the facts this change starts from, and the roles they name are
   where the units start.

## 1. Survey the shape

Read what tells you how the plugin is divided, and nothing that tells you what it says:

- `README.md`, `CLAUDE.md`, `contracts.yml`, `hooks/hooks.json` when present.
- Every agent's and skill's frontmatter, not the body:
  `for f in agents/*.md skills/*/SKILL.md; do echo "== $f"; awk 'NR==1&&/^---/{f=1;next} f&&/^---/{exit} f' "$f"; done`
- Line counts: `wc -l agents/*.md skills/*/SKILL.md skills/*/references/*.md hooks/*.py scripts/*.py skills/*/scripts/*.py 2>/dev/null`.
- `runs/audits/INDEX.md`, when the plugin has an audit ledger.
- Each eval set's ids and names: `python3 -c "import json,sys;[print(sys.argv[1],e['id'],e['name']) for e in json.load(open(sys.argv[1]))['evals']]" evals/sets/<set>.json`.

From these: which agent preloads which skill, which skill forks or spawns which agent, which
hook acts on which role, and how many lines each role loads before it reads anything.

## 2. The goal and the units, then your yes

**The goal.** One `AskUserQuestion` round of two to four questions, each with the recommended
option first, unless the argument and the survey settle it: the facts the change starts from
(the issues selected in Setup, the audits, incidents or eval logs behind it, or the rule the
plugin must now meet, named by its file); which outcomes come first (no contradictions, rules
moved from prose into scripts, less always-loaded context, every driver holding only what a
script prints, or others the user names); what is out of scope.

A goal that turns out to need a workflow that does not exist, or one redrawn from its
driver down, is `design-plugin`'s: say so before any unit runs, and stop. A goal that needs
one such piece among many edits goes on here, and that piece lands under **Needs a design**
(§5).

**The units.** Compose them from the survey:

- A wave-1 unit is one role's world (its agent, the skills it preloads or invokes, the part
  of the driver that spawns it, the hooks that act on it) or one set of scripts. It reads
  about 4,000 lines whole at most; split a role that needs more, the way the implementer's
  prose and its hooks were two units in dev-team's determinism review.
- Every file under `agents/`, `skills/`, `hooks/` and `scripts/` is in at least one unit's
  reads. Check it with the line-count listing, not from memory.
- Twelve units per wave at most.
- A synthesis wave earns its place when a concern runs across units: knowledge skills that
  several roles preload (one owner per rule), or mechanisms several units proposed (one
  design for all the guards). Each synthesis unit reads wave-1 findings of named kinds plus
  the files its concern needs.
- REC, the reconcile unit, is always the last wave and always one agent.

Show the units in chat as the plan's §7 table (Unit, Scope, Reads whole, Reads in part,
Issues, Emphasis) with the waves under it, and ask with one `AskUserQuestion`: approve, or
change something. Revise and re-show until approved.

Then write `<slug>-review-plan.md` from
`${CLAUDE_PLUGIN_ROOT}/templates/review/review-plan.md`, keeping every heading, with §5's
checks written from the goal. Commit it: `<P> <slug> (review plan): <the goal in a phrase>`.

## 3. The waves

For each wave in turn:

1. Spawn every unit of the wave **in one message**: `subagent_type: general-purpose`, the
   prompt in `references/unit-prompt.md` with its `<…>` filled from the unit's row, and
   `<plugin-dev>` as `${CLAUDE_PLUGIN_ROOT}`'s absolute path (a subagent has no such
   variable).
2. When they have returned: `E findings <P>/site/notes/<slug>/findings`. A unit whose file is
   missing or fails gets its `FAIL` lines through `SendMessage`, once, and is checked again
   (without `SendMessage`, a fresh agent with the same prompt plus the failures). A unit
   still failing is reported to the user, who decides whether the wave goes on without it.
3. Commit the wave by path: `<P> <slug> (review wave <n>): <units>`.

Do not open the findings. The returns and `E findings` are all this chat reads of them.

## 4. Reconcile

1. Spawn REC with the prompt in `references/reconcile-prompt.md`.
2. `E check <P>/site/notes/<slug>/<slug>-edits.md --findings <P>/site/notes/<slug>/findings`
   must pass, open decisions allowed: every item well formed, no dependency cycle, and every
   finding id cited by an item, a conflict or a non-goal. With
   an audit ledger, every open, recurred and wontfix id in `runs/audits/INDEX.md` must also
   appear in the list's **Issues** section (a `grep -c` per id, not a reading). Failures go
   back to REC once, as in step 3.

## 5. The decisions

`E check` names the open decisions. Read only the **Decisions taken** table (print it with
`sed -n '/^## Decisions taken/,/^## Edits/p'`), and the items a decision cites through
`E show` when a question needs their detail to be asked well.

Ask them in `AskUserQuestion` rounds of up to four, each question with its options from the
row's Alternatives and the recommended one first. Never ask what the findings settled, and
never reopen a row REC already chose.

Write each answer into its row: Chosen, and Why in the user's terms. Then, for each answer:

- When the chosen fix adds a new workflow, a new agent with its own loop, or a new file two
  workflows meet at, move the items it covers from **Edits** to **Needs a design**, whole.
  That piece is designed, not just edited. A hook, a script flag or a record file inside a
  loop that already exists is not one of these: it stays an edit, whose item gives its exact
  behavior and a fixture. Most reviews leave the section empty.
- When it makes an item moot (the user chose to keep things as they are), the item stays,
  and its `edit:` says so in one line, so `plan-phases` still sees it and its evals.

`E check --decided` must pass.

## 6. Commit and hand off

1. If the plugin has a `contracts.yml`, run `check-contracts`: `site/notes/` is in its
   scope, so a list that quotes a forbidden pattern is reworded. Fix the list, not the
   claim.
2. Commit the list, and the plan if the decisions touched it:
   `<P> <slug> (review): edit list — <n> items, <m> decisions`. Nothing is pushed.
3. Report in chat: the items by mechanism (from `E index`), the decisions and their
   answers, the issues addressed and not, and what goes next:

   > In a new chat, from `<worktree>/<P>`: `/plugin-dev:plan-phases <slug>`

   or, when **Needs a design** has items, `/plugin-dev:design-plugin <slug>` first, in a
   new chat, then `plan-phases`. Say why it is a new chat: the planner should see the edit
   list and nothing of this one, so a gap in the list shows up as a question.

## Rules

- **No unit edits a plugin file**, and neither does this chat. This skill produces findings
  and one list; the edits are `run-phase`'s.
- **This chat reads shapes and script output.** Frontmatter, line counts, the audit index,
  unit returns, `edits.py`. It never opens an agent's or skill's body, a findings file, or
  the edit list whole.
- **The list is the spec.** Anything a unit found and REC did not carry into an item, a
  conflict or a non-goal is lost. That is why REC must account for every finding id.
- **Nothing is pushed, merged or bumped here.**
