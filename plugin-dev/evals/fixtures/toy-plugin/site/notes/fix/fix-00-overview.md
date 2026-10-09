# toy fix — overview

Branch: `toy-fix`. A fixture plan for plugin-dev's `run-phase` evals, from the edit list
`fix-edits.md`. Nothing here bumps or tags anything.

## Files other files parse

None.

## Phases

One commit per phase. Commit messages begin `toy fix (phase N): <what>`.

| Phase | Note | What it adds | Items | Must not touch | Depends on |
|---|---|---|---|---|---|
| 0 | 00-overview | this plan | — | — | — |
| 1 | 01-input | greet's Input and Output headings | E-001 | greet's description | 0 |
| 2 | 02-no-name | greet's no-name line | E-002 | greet's description (phase 3's) | 1 |
| 3 | 03-hi | "hi" in greet's description | E-003 | greet's body | 0 |

## Evals by phase

| Phase | ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|---|
| 1 | F1-M1 | mechanical | `greet` | — | — | `grep -c '^## Input$' skills/greet/SKILL.md` prints 1. |
| 2 | F2-M1 | mechanical | `greet` | — | — | `grep -n 'With no name in the request' skills/greet/SKILL.md` prints exactly one line, numbered one more than the line holding `Write \`outputs/greeting.txt\``. |
| 3 | F3-M1 | mechanical | `greet` | — | — | `grep -c 'hello or hi' skills/greet/SKILL.md` prints 1. |

## Breaking changes to list in `CHANGELOG.md`

None.
