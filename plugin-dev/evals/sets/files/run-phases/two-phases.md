# Setup (the executor does this before anything else)

Copy evals/fixtures/toy-plugin/ to a fresh temporary directory OUTSIDE the repo and rename
the copy's .claude-plugin/plugin.json.fixture to plugin.json. Before the first commit, give
the plan a second phase:

- Write `site/notes/0.2/0.2-02-wave.md` with exactly the note between the `~~~` lines below.
- In `site/notes/0.2/0.2-progress.md`, add the row `| 2 | 02 | todo | | | |` after phase 1's row.
- In `site/notes/0.2/0.2-00-overview.md`'s phases table, add the row
  `| 2 | 02-wave | \`skills/wave/SKILL.md\`, verbatim in its note | the \`wave\` skill | \`skills/greet/\` | 1 |`
  after phase 1's row, and in its Evals by phase table the row
  `| 2 | T2-M1 | mechanical | \`wave\` | — | — | \`skills/wave/SKILL.md\`'s frontmatter parses as YAML with \`name: wave\` and a non-empty \`description:\`. |`.

Then `git init` the copy, commit everything as "fixture", create and check out branch
`toy-0.2`, and run the target from inside that copy's root (the directory holding
.claude-plugin/plugin.json). Every git command the target or the agents it spawns run
happens in that copy. This is the one exception to "write nothing": the temp copy is not
the repo. When done, copy its final `git log --stat` and the progress ledger into outputs/.

~~~
# 02 — wave

Phase 2. Adds the skill `wave`: it writes a one-line wave. The gap it closes: `toy` can
greet and say goodbye but not wave.

## Decisions

None — `wave` copies `greet`'s shape exactly.

## Files

| Path | Change |
|---|---|
| `skills/wave/SKILL.md` | new — verbatim below |

## Specification

`skills/wave/SKILL.md`, verbatim:

```markdown
---
name: wave
description: Wave at someone by name. Use when the user asks to wave at a person.
---

# Wave

Write `outputs/wave.txt` containing one line: `*waves at <name>*`.
```

## Steps

1. Create `skills/wave/SKILL.md` exactly as in **Specification**.
2. No `contracts.yml`, so no `check-contracts`; `site/` holds only these notes, so no
   `build-site`.
3. Evals: T2-M1 below, logged with `log-eval`.
4. Commit: `toy 0.2 (phase 2): wave`.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| T2-M1 | mechanical | `wave` | — | — | `skills/wave/SKILL.md`'s frontmatter parses as YAML with `name: wave` and a non-empty `description:`. |

## Done when

- `skills/wave/SKILL.md` exists with the frontmatter above.
- T2-M1 passes and is logged.
~~~

# User's answers

- When the target relays a review of eval results: **before answering**, run
  `git log --oneline` in the temp copy and save it to `outputs/git-log-at-review-<N>.txt`,
  N being the phase under review. Then answer: "Reviewed — approve, commit it."
- When it asks which phases to run, or whether to go on: all of them.
- Anything else: the option marked Recommended.
