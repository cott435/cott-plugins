# NN — <name>

Phase NN. <One paragraph: what this phase adds or changes, and the gap it closes. Written
for an agent that has read only the spec, the overview, the ledger, and this note.>

## Decisions

<Anything settled here rather than in the design: a name, a default, a placement. Each
with its reason. "None" if none.>

## Files

| Path | Change |
|---|---|
| `agents/<name>.md` | <the section, named by its heading or by text quoted from it: what is inserted, replaced, or removed. Never a line number: the phases before this one move lines, and the builder finds the quoted text where it is> |
| `skills/<name>/SKILL.md` | new — frontmatter below |
| `contracts.yml` | <entries added, by kind; a shared file every phase may add to> |

<Every path here is one the overview's Phases row gives this phase under Files, a shared
file, or a file this phase creates. Another phase's file is never a row.>

## Specification

<The exact content. Frontmatter blocks verbatim. Heading names verbatim, in the order they
appear. Rules quoted as they will read in the file. Column names of any table another file
parses. Every edit anchored on text quoted from the file as it is now, long enough to be
found once with `grep -nF`. Where a rule lives in one file and is cited from others, name
the owner and the readers — that is the `contracts.yml` entry.>

## Steps

1. `phases.py brief`, then every anchor this note quotes found as it stands (`grep -nF`).
2. <Edit, in the order that keeps the bundle consistent after each step.>
3. The plugin's own rules for an added or removed file (its `CLAUDE.md`).
4. `phases.py checks`: `check-contracts`, the plan's own checks, `build-site` at the last phase only.
5. Evals — the table below, run with `run-evals` (it stops for review when a row is
   behavioral) and logged with `log-eval` before results are reported.
6. `phases.py finish --what "<what>" --log … --iteration …`: the ledger row and the commit
   `<plugin> <slug> (phase NN): <what>`.

## Evals

<!-- This phase's rows from the overview's Evals by phase, copied; a pass bar is never
     loosened here. Kind is one of run-evals' kinds: mechanical · load · behavioral · trigger ·
     platform-fact. Only a checkpoint phase has behavioral rows; each names its set file and
     eval IDs. Baseline `working tree only`: run-evals starts no baseline for that row. -->

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| <ID> | <kind> | <skill or agent> | <none / previous / ref / working tree only> | <evals/sets/x.json 1,2> | <checkable condition> |

## Done when

<Conditions a reader can check without judgment: a command's output, a file's presence,
a count, a logged eval's verdict.>

<!-- plan-phases' unit planner writes this note when the plan is written, from the overview's
row, the spec's items and the files as they are then (run-phase writes it when the phase
starts, for a plan from before notes were written there). run-phase appends `## Deviations`
below when the note could not be followed as written: what the note said, what was done,
why. A new note has no Deviations section. -->
