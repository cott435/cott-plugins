# toy fix — edit list

Reviewed 2026-10-09. Mode: review. Branch `toy-fix`, against `fixture` (toy 0.1.0).

A fixture edit list for plugin-dev's `plan-phases` and `run-phase` evals. Its line numbers
are `skills/greet/SKILL.md` as it was when reviewed, eight lines long; phase 1 has since
added the Input and Output headings, so every later line has moved.

## Goal

`greet` states its input and its no-name case, and triggers on "hi" as well as "hello".

## Decisions taken

| ID | Decision | Chosen | Alternatives | Why | Items | Origin |
|---|---|---|---|---|---|---|
| D-01 | What greet writes when the request has no name | `Hello.` | (a) `Hello.`; (b) ask for the name | A one-line output stays one line; asking breaks the skill's single write | E-002 | review |

## Edits

### E-001 greet never says where the name comes from
- findings: F-G-01
- files: skills/greet/SKILL.md:6
- mechanism: prose
- edit: after `# Greet` (line 6), add an `## Input` section, "The person's name, from the user's request.", and an `## Output` heading before the Write line.
- depends: none
- decide: none
- closes: none
- evals: none
- fixture: none

### E-002 greet has no rule for a request with no name
- findings: F-G-02
- files: skills/greet/SKILL.md:8
- mechanism: prose
- edit: directly after the line "Write `outputs/greeting.txt` containing one line: `Hello, <name>.`" (line 8), add the line "With no name in the request, write `Hello.` instead."
- depends: E-001
- decide: D-01
- closes: none
- evals: none
- fixture: none

### E-003 greet's description misses "hi"
- findings: F-G-03
- files: skills/greet/SKILL.md:3
- mechanism: prose
- edit: line 3's description → "Greet someone by name. Use when the user asks to say hello or hi to a person."
- depends: none
- decide: none
- closes: none
- evals: none
- fixture: none

## Needs a design

None: every fix changes what exists.

## Conflicts

None.

## Platform facts

None: no item relies on a platform behavior.

## Build order

1. E-001: the headings the other edits sit under.
2. E-002, after E-001.
3. E-003, independent.

The smallest slice is E-001 alone.

## What must not break

`greet`'s name and its one-line output to `outputs/greeting.txt`.

## Issues

No audit ledger: the fixture has none.

## Context budget

Deleted: the goal is not about context.

## Non-goals

None.
