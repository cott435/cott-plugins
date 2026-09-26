# <plugin> <slug> — design

Approved <date>. Mode: <new | change>. Branch `<plugin>-<slug>`.

Written by `design-plugin` from the discussion, and approved in two gates: the charts, then
this writeup. `plan-phases` reads it, in a chat that has seen nothing else, to write the phase
notes and their evals. `run-phase` reads it for the why. Anything decided in the discussion and
not written here is lost.

<!-- The section list and its order are owned by design-plugin's SKILL.md, "3. The writeup".
     Lines marked (change) or (new) apply to that mode; delete the other. -->

## The idea

<One paragraph, in the user's terms, of what exists when this is built. (change) What is wrong
today and what the change makes true, citing the review, eval or incident behind it.>

## Workflows

### <workflow name>

<Trigger → deliverable, one line.>

```mermaid
flowchart TB
  %% the approved chart for this workflow
```

- **Unit:** <what one instance reads, and the file it writes, with that file's fields>
- **Strengthened by:** <structure, evaluator, revision cap, never-claim rules, and why>

| Input | Supplied by |
|---|---|
| <which units to run on> | <the user: argument / config file · file: path, written by loop · loop: name> |

## How they fit together

```mermaid
flowchart TB
  %% the approved system chart: loops, typed commands, the files where they meet
```

| File | Written by | Read by | Fields read | Stale when |
|---|---|---|---|---|
| | | | | |

## Components

| Name | Kind | Role | Reads | Writes | Used by | Origin |
|---|---|---|---|---|---|---|
| | agent / workflow skill / knowledge skill / script | | | | | asked / composed / suggested: why |

## Outputs

### `<path>`

- Sections: <in order>
- Cites: <what every claim in it must point to>
- Never claims: <the domain rules>
- Stale when: <the input change that makes it stale>

## Cost

| Workflow | Cold run reads | Warm run reads | Horizon |
|---|---|---|---|
| | | | |

## Decisions taken

| Decision | Chosen | Alternatives | Why | Origin |
|---|---|---|---|---|
| | | | | asked / suggested |

## Platform facts

| Fact | Status | Source or expected answer |
|---|---|---|
| | verified / assumed | <the doc checked, or the answer expected; an assumed fact becomes a phase-0 eval> |

## Build order

<Which components depend on which, bottom-up. Then the smallest slice that works end to end:
the one loop and the thinnest workflow that uses it. Not the phases; plan-phases splits those
from this.>

## What must not break

<(change) Headings other files parse, commands users already type, defaults, and every breaking
change a user will notice with what to do about it. (new) Delete this section.>

## Non-goals

<What this deliberately does not do, and why. Each declined suggestion: one line, what was
suggested and that it was considered and declined.>
