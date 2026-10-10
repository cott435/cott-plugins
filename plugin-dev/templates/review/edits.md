# <plugin> <slug> — edit list

Reviewed <date>. Mode: review. Branch `<plugin>-<slug>`, against `<sha>` (<plugin> <version>).

<!-- The last commit this paragraph names in backticks is the one every item's line numbers
     belong to: `scripts/edits.py show --located` carries them from it to the tree as it
     stands. -->

Written by the reconcile unit of `review-plugin` from every findings file under `findings/`,
with the decisions answered by the user. It is the spec for this change, the way a design is
for one that starts from an idea: `plan-phases` assigns every item below to one phase, and
`run-phase` reads only its phase's items through `scripts/edits.py show`. Anything not
written here is lost.

<!-- This template is the one list of the edit list's sections: keep every `##` heading, in
     this order. plan-phases and run-phase read it by these names, scripts/edits.py parses
     Edits and Decisions taken, and check-contracts fails when a skill names a section this
     file does not have. -->

## Goal

<The review plan's goal, as approved: the outcomes in priority order, and how a reader could
tell each one holds.>

## Decisions taken

<One row per choice the reconcile unit could not make on the findings alone: the user's.
REC writes the rows with Chosen `open`; review-plugin asks them and fills Chosen and Why.
plan-phases adds a row with Origin *planning* for every gap it asks about, here and not in a
design read beside this list, which keeps its table as approved.>

| ID | Decision | Chosen | Alternatives | Why | Items | Origin |
|---|---|---|---|---|---|---|
| D-01 | <the question> | open | <(a) …; (b) …, one line each, the recommended first> | | <E-ids> | review |

## Edits

<One block per item, ordered so an item's dependencies come before it: contradictions, then
the underspecified prose a mechanism will parse, then the mechanisms in dependency order,
then contracts and evals, then cuts and moves. Group headings (`### A. Contradictions`) are
allowed between blocks. Two findings about one rule are one item citing both.>

### E-001 <the defect, in one line>
- findings: <F-ids>
- files: <path:line, path:line>
- mechanism: prose | hook | script | contracts.yml | eval
- edit: <the one edit, as a fresh chat would make it. For a decide item: one line per option, `(a) …` `(b) …`>
- depends: <E-ids this item needs landed first | none>
- decide: <D-id | none>
- closes: <audit issue ids | none>
- evals: <set and ids to re-run; `new <set> <n> <name>` for an eval to write>
- fixture: <for a script: input → expected output | none>

## Needs a design

<Items whose chosen fix adds a new workflow, a new agent with its own loop, or a new file two
workflows meet at. They are not under Edits: they go through `design-plugin <slug>` on this
branch, which reads this section as the change it designs, and `plan-phases` plans the design
and this list together. A hook, a script flag or a record file inside a loop that already
exists is an edit, not a design: its item gives the exact behavior and a fixture. "None" when
every fix changes or adds to what exists, which is the usual case.>

## Conflicts

<Where the units disagreed: the sides with their finding ids, the choice made and why. A
choice that is the user's points to its D-id instead.>

## Platform facts

<Every Claude Code behavior an item relies on that `plugin-anatomy` does not mark [docs] or
[proven].>

| Fact | Status | Source or expected answer | Items |
|---|---|---|---|
| | verified / assumed | <the plugin-anatomy reference checked, or the answer expected; an assumed fact becomes a phase-0 eval> | |

## Build order

<Layers, bottom-up, each a line of E-ids with what it proves: a layer depends on the ones
above it unless marked independent. Then the smallest slice that works end to end. Not the
phases; plan-phases splits those from this.>

## What must not break

<Headings other files parse, commands users type, flags and defaults, and every breaking
change a user will notice with what to do about it.>

## Issues

<Every open, recurred and wontfix audit issue, and the item that addresses it or
`not addressed — <why>`. Delete the section, with a line saying so, when the plugin has no
audit ledger.>

| Issue | Status | Item |
|---|---|---|

## Context budget

<What each role loads before it reads a repo file, now and after every item. Delete the
section, with a line saying why, when the goal is not about context.>

## Non-goals

<What this review deliberately leaves alone, and why.>
