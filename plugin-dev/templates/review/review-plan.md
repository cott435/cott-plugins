# <plugin> <slug> — the review plan

A review of `<plugin>`, run as parallel agents that each read one part of the bundle and
write findings to one file, then <n> synthesis units, then one reconcile unit. The output is
`<slug>-edits.md`: one deduplicated list of edits, each with its files and lines, its
mechanism and the evals that prove it. `plan-phases` plans from it in a fresh chat.

Written <date> against `<branch>` at `<sha>` (<plugin> <version>). Inputs: <the bundle's
agents, skills, hooks and scripts; the audit ledger's n issues; the eval set names>.

<!-- revise-plugin writes this from the approved goal and units. Keep every `##` heading.
     Brief, Checks and Finding format are the charge every unit gets; the unit rows say
     what each one reads. The finding format and the findings-file shape are fixed by
     templates/review/findings.md and checked by scripts/edits.py: do not change them here. -->

## 1. Goal

<The outcomes, in priority order, as approved. Each says what is true after the fixes and
how a reader could tell. Then: what is out of scope, and that no unit edits a plugin file.>

## 2. Where things are written

- Branch `<plugin>-<slug>`, in the worktree `<path>`. This chat commits after each wave;
  nothing is pushed.
- This plan: `<plugin>/site/notes/<slug>/<slug>-review-plan.md`.
- One findings file per unit: `<plugin>/site/notes/<slug>/findings/<UNIT>.md`. A unit writes
  exactly that file, and reads another unit's file only when its row says so.
- The edit list: `<plugin>/site/notes/<slug>/<slug>-edits.md`, written by the reconcile unit.

## 3. Waves

| Wave | Units | Runs | Reads |
|---|---|---|---|
| 1 | <ids> | n in parallel | the plugin files in each row |
| 2 | <synthesis ids, or "none"> | n in parallel | wave-1 findings of the kinds each row names |
| 3 | REC | 1 | every findings file, the audit index |

## 4. Brief — the charge every unit gets

You are reviewing the definition of one part of `<plugin>`: the files one role loads in a
run, or one set of scripts. You are not running the plugin and not fixing it. You read the
files, hold them against each other <and against the audit issues>, and write findings a
fresh chat can act on one at a time without you.

A rule is a finding only when it does one of the things in §5. Style preferences, rewrites
for their own sake, and rules you merely disagree with are not findings.

Read with the Read tool, whole files; Grep locates a phrase, it never replaces reading the
file a row names. Read nothing under `site/notes/`, `site/docs/` or `evals/*.md`. Quote lines
as `path:line`, with line numbers from the files as they are on this branch.

A finding of kind `prose-to-script` says what the script would read and what it would print
or refuse. "A hook could check this" is not a finding.

<Anything else every unit needs: the plugin's terms, what its scripts already enforce.>

## 5. Checks — what each unit does, in order

<The checks, numbered, written from the goal. The usual ones for a plugin:>

1. **Contradictions.** Two statements one run loads that cannot both be followed: within a
   file; an agent against a skill it preloads or invokes; an agent against the prompt its
   driver sends; prose against what a hook refuses; a return form against what the driver
   branches on. Quote both sides.
2. **Underspecified.** A step whose input, output or branch is not stated, so two runs would
   differ; a return form with no line for a case the role reaches; a term used before it is
   defined.
3. **Rules a script could enforce.** Every never / always / only / must / before / after
   about tool use, paths, file shape, order, counts or state: what enforces it now, and if
   nothing does, the mechanism (hook event or script, keyed on what, reading what, printing
   or refusing what), or why it cannot be enforced.
4. **Duplication.** One rule stated in two files, or in different words across roles. Name
   the one file that should own it.
5. **Bloat.** Rationale that does not change behavior, examples that repeat the rule,
   version history, a paragraph a hook makes redundant. Count the lines. Say which cuts
   move to a `references/` file instead of going.
6. **Inputs and return.** The fields a spawn prompt sends against the inputs the agent
   reads; every exit has a closed return form the driver branches on.
7. **The issues.** For each audit issue that names this part: is the rule still where the
   issue says; did the fix land; for a recurred or wontfix one, why prose did not hold.
8. **The evals.** Which evals pin behavior a proposed edit would change, by set and id.

## 6. Finding format

The shape is `templates/review/findings.md`'s, and `scripts/edits.py findings` checks it.
Ids are `F-<UNIT>-<nn>`.

## 7. Units

<One row per unit. A unit reads about 4,000 lines whole at most; split a role that needs
more. Twelve units per wave at most.>

| Unit | Scope | Reads whole | Reads in part | Issues | Emphasis |
|---|---|---|---|---|---|
| **<ID>** | <one role or one set of scripts> | <files> | <file §section> | <ids or none> | <what to look hardest at, beyond §5> |

## 8. Synthesis and reconcile

| Unit | Reads | Writes |
|---|---|---|
| **<ID>** | <wave-1 findings of kinds …; files whole> | `findings/<ID>.md`: <the cross-cutting view, one owner per rule> |
| **REC** | every file under `findings/`, `runs/audits/INDEX.md` | `<slug>-edits.md`, in the shape of `templates/review/edits.md` |

## 9. Between waves

The orchestrating chat reads unit returns and `scripts/edits.py` output, and not the plugin
files or the findings themselves. After each wave it runs `edits.py findings`, sends a unit
its failures once, and commits the wave. After REC it runs `edits.py check`, asks the open
decisions, records the answers, runs `edits.py check --decided`, and commits.
