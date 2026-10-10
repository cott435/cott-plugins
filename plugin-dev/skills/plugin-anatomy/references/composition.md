# Composition: how skills and agents work together

The component files say what each piece can do. This one says how to divide a design's work
between them. Platform facts here cite `skills.md` and `agents.md` rather than restating
their evidence.

## The three roles

| Role | Holds | Does not hold |
|---|---|---|
| **Workflow skill**: the orchestrator, in the main thread | Which agents run, in what order, how wide each fan-out is, where the user approves, what gets committed | The method of any one job, which belongs to an agent, or knowledge several jobs share, which belongs to a knowledge skill |
| **Agent**: one way of working, done expertly | Its role, what it reads, the contract for its output, when it stops, the judgment rules that belong only to its job, its tools and model | Orchestration (it cannot ask the user, and it should not decide what else runs), or knowledge another agent also needs |
| **Knowledge skill**: shared method or material | Templates, checklists, style guides, domain methods, anything two agents or workflows would otherwise each carry | Instructions about when to run or whom to spawn |

The main thread orchestrates because it is the only place that can ask the user. That is a
platform fact (`agents.md`), not a style choice: a design that puts a user decision inside an
agent has no way to make it.

## What goes in the agent file

- **Identity and scope**: one sentence of what it is and one of what it never does.
- **Inputs**: exactly what it is given (paths, a mode, a question) and what it reads.
- **Method**: the steps specific to this job. A step that is really a shared method is a
  skill, and the agent points to it.
- **Output contract**: the file it writes, with its sections and rules, and the message it
  returns (a short summary, the path, any questions it could not settle).
- **Stop conditions**: when it is done, when it gives up, and what it returns then.

Keep it stable. An agent file that changes with every new use is holding knowledge that
belongs in a skill.

## Attaching skills to an agent

Two ways, with different costs:

| | Preload: `skills:` in the agent's frontmatter | On demand: the agent invokes the `Skill` tool |
|---|---|---|
| Loaded | at every spawn, full content | only when the agent decides it needs it |
| Cost | the skill's full size × every instance; a fan-out of 20 pays 20 times | nothing until used |
| Reliability | always present | the agent must recognize the need; test it |
| Use for | what shapes *every* run: the template it fills, the style it writes in, the checklist it applies | situational knowledge: a debugging method used only when a test keeps failing |
| Requires | nothing | `Skill` in the agent's `tools` |

Several skills on one agent is normal: preload the one or two that define its work, and name
the situational ones in its body with when to invoke each. If an agent preloads more than a
few, check the size against its fan-out width, and whether some are only sometimes needed.

**One skill shared by many agents** is the point of a knowledge skill. When the agent
depends on the skill's headings or names, write a `contracts.yml` claim (`headings` or
`names_listed`) so a rename in the skill fails the sweep instead of an agent.

**Skills that only agents use** get `user-invocable: false`, so they stay out of the `/`
menu. A typed workflow skill that an agent must never start has `disable-model-invocation:
true`.

## Choosing between a forked skill and an agent

Both run in an isolated context.

- **Forked skill**: one entry point a person types, doing one job and returning a result.
  Nothing else spawns it.
- **Agent**: a method that workflows spawn, often many at once, with a fixed tool list and
  model. Several workflows can share it.

When the same isolated job is typed by a person *and* spawned by workflows, make it an agent
and give the person a thin workflow skill that spawns it.

## Tools and models

- **Least privilege.** List `tools` explicitly for every plugin agent. A reviewer that only
  reads gets no `Write`, or writes only its findings file. An agent that must never spawn
  others does not get `Agent`.
- **Model per role.** A cheap, wide loop (a survey, a classifier, a per-unit pass over
  hundreds of items) takes a cheaper model; the loop where judgment is made takes the
  strongest. Pinned models are recorded in the plugin's `VERSIONING.md`, so a model change is
  not mistaken for a prompt regression.

## A workflow that runs for a long time: the script holds the state

A workflow skill that keeps other agents going — one per phase, one per section — is a
*driver*. Its cost is its turns times its context, and both grow with the run, so what a
driver holds decides what the whole run costs. These are design rules, not platform facts;
the run they were measured on is in `plugin-dev/evals/2026-10-10-run-evals-runner-mechanical.md`.

- **The state of the run lives in files, and a script reads them.** Where a run stands —
  the next step, whether the last one landed, what is left — is printed by a script from the
  repo and a ledger, one line or one block, with an exit code for each outcome. The driver
  runs the script and acts on the code; it does not open the ledger or the plan and work it
  out. (`dev-team`'s `status.py`; `plugin-dev`'s `scripts/phases.py`.)
- **A driver carries three things**: what the script printed, what each agent returned in a
  fixed form, and the user's answers. It keeps the work going, reports counts, and routes a
  question to the user and the answer back to the agent that asked. It reads no file an
  agent could read for itself and does none of the work.
- **Each agent gets its slice, printed.** A script prints the part of the plan one agent
  needs. An agent that reads the whole plan to find its row pays for every other row on
  every turn.
- **A record is written by a script, not by hand.** A ledger row, a commit that closes a
  step, an index line: the script that checks the step is whole writes them, and refuses
  when it is not. A check a model performs by reading is a check that is sometimes skipped.
- **Fan-out is waited on by a script.** Many runs started one tool call each wake the
  driver once each, and every wake re-reads its context: on one plan that cost as much as
  all the runs together. One background command starts them, waits, and prints one report.
- **What must hold is a hook; what must be known is a script's output; what is left is
  judgment**, and only that is the model's. When a rule is being written into a driver's
  prose for the third time, it belongs in one of the first two.

## Where hooks and MCP servers fit

- A rule an agent must never break is enforced by a **plugin hook** (`hooks/hooks.json`),
  not by the agent's own `hooks:` field, which plugin agents ignore (`agents.md`). A
  `PreToolUse` hook sees `agent_type` in its input, so it can apply to one agent only.
- A skill's own `hooks:` field registers hooks when the skill is invoked, and they stay for
  the rest of the session. Use it for a guard that should exist only once a workflow has
  started (`hooks.md`).
- An external system an agent needs is a **plugin MCP server** (`.mcp.json`), and the agent
  lists its tools by full name, `mcp__plugin_<plugin>_<server>__<tool>`, in `tools` (`mcp.md`).

## Anti-patterns

- **One agent per command.** Commands and agents are counted separately; a 1:1 match means
  the work was not composed (see `design-plugin`'s composing reference).
- **Rules in the plugin's `CLAUDE.md`** meant for agents or skills at runtime. It is never
  loaded as plugin context (`agents.md`).
- **The same checklist pasted into three agents.** Make it a skill; preload or invoke it.
- **An agent that asks the user.** It cannot. Return the question.
- **A driver that reads the plan.** A skill that keeps a run going and opens the ledger,
  the plan or its agents' outputs to decide what is next. Print it from a script.
- **A hook where an instruction would do**, or an instruction where only a hook would do.
  A hook runs in every session the plugin is enabled in, so it earns its place only when
  "almost always" is not good enough.
