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
- **A hook where an instruction would do**, or an instruction where only a hook would do.
  A hook runs in every session the plugin is enabled in, so it earns its place only when
  "almost always" is not good enough.
