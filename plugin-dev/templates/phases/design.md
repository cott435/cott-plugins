# <plugin> <slug> — design

Approved <date>. Mode: <new | change>. Branch `<plugin>-<slug>`.

Written by `design-plugin` from the discussion, and approved in two gates: the charts, then
this writeup. `plan-phases` reads it, in a chat that has seen nothing else, to split the phases
and write their evals. `run-phase` reads it to write each phase's note, and for the why. Anything decided in the discussion and
not written here is lost.

<!-- This template is the one list of the design's sections: keep every `##` heading, in this
     order. plan-phases reads the design by these names, and check-contracts fails when it
     names one this file does not have. Lines marked (change) or (new) apply to that mode; delete the other. -->

## The idea

<The restated idea, as approved at the charts gate: one paragraph, in the user's terms, of what exists when this is built. (change) What is wrong
today in the workflow being changed and what the change makes true, citing the eval or incident behind it.>

## Workflows

<One `###` per workflow, each with its approved chart.>

### <workflow name>

<Trigger → deliverable, one line.>

```mermaid
flowchart TB
  %% the approved chart for this workflow
```

- **Driver:** <the typed skill that drives this workflow in the main thread, and what it
  holds: what the script prints, what each agent returns, the user's answers. Nothing else>
- **Where the run stands:** <the script and its command that prints the next step and each
  agent's slice, with an exit code per outcome; the ledger it reads, either a file and what
  one row holds, or "derived" and from which files; and the command that checks a step and
  writes its row. A workflow of one step: "one step, no ledger">
- **Returns:** <one entry for every agent in this workflow's chart, an agent another workflow
  also spawns included: its closed list of statuses, and what the driver does on each>
- **Held by:** <the hook behind each step that must pass before its agent stops, and behind
  each write scope; or "nothing must hold" and why>
- **Unit:** <what one instance reads, and the file it writes, with that file's fields>
- **Strengthened by:** <structure, evaluator, revision cap, never-claim rules, and why>

| Input | Supplied by |
|---|---|
| <every input the unit needs besides its source: which units to run on, what to look for, what to judge against> | <the user: argument / config file · file: path, written by loop · loop: name> |

## How they fit together

```mermaid
flowchart TB
  %% the approved system chart: loops, typed commands, the files where they meet
```

<One row for every file two loops meet at.>

| File | Written by | Read by | Fields read | Stale when |
|---|---|---|---|---|
| | | | | |

## Components

<The components table approved at the charts gate.>

| Name | Kind | Role | Reads | Writes | Used by | Origin |
|---|---|---|---|---|---|---|
| | agent / workflow skill / forked skill / knowledge skill / hook / MCP server / script / config | | | | | asked / composed / suggested: why |

## Outputs

<One `###` for every file a reader depends on.>

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

<Every decision from the discussion. Origin: asked, or suggested and accepted; plan-phases adds
planning for a gap it asked about, unless an edit list sits beside this design, which then
takes the answer.>

| Decision | Chosen | Alternatives | Why | Origin |
|---|---|---|---|---|
| | | | | asked / suggested |

## Platform facts

| Fact | Status | Source or expected answer |
|---|---|---|
| | verified / assumed | <the plugin-anatomy reference or doc checked, or the answer expected. An assumed fact becomes a phase-0 eval, and its result is written back to plugin-anatomy> |

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
