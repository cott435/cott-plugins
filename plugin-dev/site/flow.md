# The flow

The map of plugin-dev: which route a change takes, which role uses which skill, who writes
and reads each document, and how each driver keeps its run in files. The workflow pages walk
each route step by step.

## Which route

A plugin exists to run workflows on their own: a thin driver in the main chat, the agents
it spawns, and the scripts, hooks and ledger that keep a run on track (`plugin-anatomy`).
A change to one reaches the plugin by where it starts.

| The change starts from | And is | Type | Page |
|---|---|---|---|
| an idea | a new plugin, or a workflow added or redrawn | `/plugin-dev:design-plugin` | [Designing a plugin or a workflow](workflows/design-a-workflow.md) |
| facts about the plugin | a few audited issues (`issues.py route` exits 0) | `/plugin-dev:fix-issues` | [Changing a plugin from facts](workflows/revise-from-facts.md) |
| facts about the plugin | many issues, or a rule every agent and skill must meet | `/plugin-dev:revise-plugin` | [Changing a plugin from facts](workflows/revise-from-facts.md) |
| a spec either route committed | to be built | `/plugin-dev:plan-phases`, then `/plugin-dev:run-phases` | [Planning and running the phases](workflows/plan-and-run-phases.md) |
| a run of the plugin's workflow | to be checked against the plugin's files | `/plugin-dev:audit-run` | [Checking a run, and checking the fix](workflows/audit-a-run.md) |

One agent or skill edited in place needs none of these: read its `plugin-anatomy`
reference, edit, `check-contracts`, `build-site`, `run-evals` on its set when the edit
changes what it does, one commit.

## Agents and skills

The roles are the typed skills that drive a workflow from your chat, the agents they spawn,
and the two agents this plugin ships. A role marked here runs that skill itself; a driver
does not inherit what its agents run.

<!-- flow:agents-skills -->

## Who writes what

Every hand-off between chats is a file. An arrow runs from a role to a document it writes.

<!-- flow:writes -->

## Who reads what

An arrow runs from a document to a role that reads it. A driver reads a ledger or a spec
through a script's output, never whole.

<!-- flow:reads -->

<!-- flow:documents -->

## How the drivers run

A driver holds only what its script prints, what each agent returns and your answers. Where
the run stands is in a ledger on disk: a script reads it and prints the next step, the
driver spawns an agent for that step, and the step's result goes back into the ledger
through one writer. Typed again in a new chat, a driver starts from the ledger and picks up
where it says.

<!-- flow:drivers -->

`design-plugin` and `plan-phases` drive short runs that end at your yes, so they keep no
ledger of their own: what they leave is the spec and phase 0.
