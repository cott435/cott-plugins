# NN — <name>

Phase NN. <One paragraph: what this phase adds or changes, and the gap it closes. Written
for a chat that has read only the design, the overview, the ledger, and this note.>

## Decisions

<Anything settled here rather than in the design: a name, a default, a placement. Each
with its reason. "None" if none.>

## Files

| Path | Change |
|---|---|
| `agents/<name>.md` | <section: what is inserted, replaced, or removed> |
| `skills/<name>/SKILL.md` | new — frontmatter below |
| `contracts.yml` | <entries added, by kind> |

## Specification

<The exact content. Frontmatter blocks verbatim. Heading names verbatim, in the order they
appear. Rules quoted as they will read in the file. Column names of any table another file
parses. Where a rule lives in one file and is cited from others, name the owner and the
readers — that is the `contracts.yml` entry.>

## Steps

1. <Edit, in the order that keeps the bundle consistent after each step.>
2. …
3. The plugin's own rules for an added or removed file (its `CLAUDE.md`).
4. `check-contracts` (if `contracts.yml`); `build-site` (if `site/`).
5. Evals — the table below, run with `run-evals` (it stops for review when a row is
   behavioral) and logged with `log-eval` before results are reported.
6. Commit: `<plugin> <slug> (phase NN): <what>`.

## Evals

<!-- Kind is one of run-evals' kinds: mechanical · load · behavioral · trigger · platform-fact.
     A behavioral row names its set file and eval IDs; the prompts are in that set already. -->

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| <ID> | <kind> | <skill or agent> | <none / previous / ref> | <evals/sets/x.json 1,2> | <checkable condition> |

## Done when

<Conditions a reader can check without judgment: a command's output, a file's presence,
a count, a logged eval's verdict.>

<!-- run-phase appends `## Deviations` below when the note could not be followed as
written: what the note said, what was done, why. plan-phases leaves it absent. -->
