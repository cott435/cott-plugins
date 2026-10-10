---
name: plugin-anatomy
description: The source of truth for what each Claude Code plugin component is for and exactly how it behaves - skills, agents, hooks, MCP servers, the manifest, and the rarer ones - with the shape every workflow takes (a thin driver in the main chat that spawns agents and is kept on track by scripts, hooks and a ledger), the routing rules for which component a responsibility belongs in, and the edge cases that fail silently. Every fact carries its source and whether it is documented, proven by an eval, or unconfirmed. Use when designing or planning a plugin or one of its workflows, writing or reviewing the skill that drives a run, deciding whether something should be a skill, agent, hook, MCP server or script, writing or reviewing frontmatter, hooks.json, .mcp.json or plugin.json, or when a platform fact about plugins is in question. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json) or the marketplace repo that holds it.
---

# Plugin anatomy

This skill is the one place a plugin-dev skill, or a person building a plugin, looks up what
a component can do and how a workflow is built from them. `design-plugin` routes
responsibilities with it, `plan-phases` copies frontmatter from it, `run-phase` reads it
before creating a component, and `check-contracts` reads its allowed-key lists. A fact stated anywhere else in plugin-dev cites the file here
instead of restating it, so when the platform changes there is one place to fix.

## How to trust a fact here

Every fact ends with its status:

- **`[docs]`**: stated in the Claude Code docs. Each reference file lists its pages under
  **Sources**, with the date and Claude Code version they were read against.
- **`[proven: evals/…]`**: shown by one of this repo's own eval runs; the log is the evidence.
- **`[unconfirmed]`**: believed but not settled. Nothing may depend on it. A design that needs
  it writes it down as an *assumed* platform fact, and `plan-phases` turns it into a phase-0
  `platform-fact` eval.

When a `platform-fact` eval settles something, write the result back here in the same
change that logs it: update the fact's status to `[proven: <log>]`, or correct the fact and
cite the log. A fact proven in another plugin's plan is written back here as a small change
to plugin-dev. The docs change faster than this file, so where a fact and the docs disagree,
the docs win, and the fact is corrected here and marked with the date it was re-read.

## What a plugin is for: a workflow that runs itself

A plugin exists to run a workflow autonomously. The user types one command in the main chat,
and the work goes on, step after step, until it is done or something needs them. Design
every workflow as these six parts, and start from the first:

| Part | What it is | Its job |
|---|---|---|
| **Driver** | the workflow's typed skill, inline in the main thread | Runs the loop: asks a script what is next, spawns the agent for it, takes the return, has a script record it, asks again. Carries questions to the user and answers back. Does none of the work |
| **Agents** | `agents/*.md`, spawned by the driver as needed | Do the work, one step each in a fresh context, and return in a fixed form |
| **Scripts** | code the driver, an agent or a hook runs | Answer everything that is a lookup or a check: where the run stands, one agent's slice of the plan, whether a step is whole |
| **Hooks** | `hooks/hooks.json` | Hold what must hold whatever a model decides: where an agent may write, what a step must pass before its agent stops |
| **Ledger** | files in the user's project, written by a script | Records what is done and by what evidence, so what is next is read and never remembered |
| **Knowledge skills** | skills the agents preload or invoke | Carry the methods and templates more than one agent needs |

Three rules decide most of a design:

1. **The driver is thin.** It is the one context that lasts the whole run, and every turn
   re-reads all of it, so what it holds is paid for on every step after. It holds what the
   script printed, what each agent returned, and the user's answers. It reads no plan, no
   ledger and no agent's output, and it does no step itself.
2. **The run is deterministic wherever it can be.** What must hold is a hook. What must be
   known is a script's output. What is left is judgment, and only that is a model's: the
   agent's inside its step, never the driver's about where the run stands.
3. **The run lives in files.** What is done and what is next are in the ledger, so the same
   command typed in a new chat picks up where the last one stopped, and anything a run
   claims can be checked afterwards.

These are design rules, not platform facts. `references/composition.md` has the driver's
loop step by step, what a ledger holds and who writes it, the hooks a run needs, how skills
attach to agents, and how small a driver gets for a small workflow. Read it before
designing a workflow or writing a driver.

## Routing: which component a responsibility belongs in

The shape above says which parts a workflow has. These questions say which part one
responsibility belongs in. Ask them in order; the first *yes* is usually the answer.

1. **Must it happen every time, whatever the model decides?** A block, a guard, a gate a
   step must pass, a format step after every edit, context injected at session start.
   → **hook**. Only a hook is deterministic; an instruction in a skill is a request the
   model can miss.
2. **Is it a deterministic transform** (count, filter, validate, convert, fetch a list), or
   a question about the run itself (what is next, did the last step land, what is left)?
   → **script**, in the skill's `scripts/`, or in the plugin's `bin/` when Claude should run
   it as a bare command (but `bin/` blocks installation on claude.ai and Cowork).
3. **Does it talk to an external system that has auth or state?** → **MCP server**, when
   WebFetch or a script calling the API cannot do it cleanly.
4. **Does it keep a run going** (start the agent for the next step, act on what it
   returned), **or need the user partway through**, to answer a question or approve
   something? → the **driver**: the workflow's typed skill, inline in the main thread, not
   forked. Subagents, and therefore forked skills, never get `AskUserQuestion`.
5. **Is it a way of working done repeatedly, in parallel, or in a context kept clean of the
   rest?** → **agent**, spawned by the driver.
6. **Is it a self-contained procedure the user starts, that returns a result without
   asking anything?** → **skill with `context: fork`**, keeping the work out of the main
   context.
7. **Is it knowledge** (a method, a template, a checklist, a style) needed when a topic comes
   up, or by more than one agent? → **knowledge skill**, model-invoked or preloaded by agents.
8. **Is it a per-user setting** (an endpoint, a token, a default)? → **`userConfig`** in
   `plugin.json`.
9. **Is it state that must outlive a session?** Where a run stands is the **ledger**: files
   in the user's project, written by a script. Anything else goes in the project or under
   `${CLAUDE_PLUGIN_DATA}`. Never under `${CLAUDE_PLUGIN_ROOT}`, which is replaced on every
   update.

Rarer components (output styles, LSP servers, monitors, themes, workflows, legacy commands,
the plugin `settings.json`) are in `references/other.md`. Reach for one only when a design
names the need it exists for.

## Components at a glance

| Component | Strength | Costs and limits | Read |
|---|---|---|---|
| Knowledge skill | Name and description are the only context cost until it is used; references load on demand | Triggering is probabilistic; the listing truncates `description` + `when_to_use` at 1,536 characters | `references/skills.md` |
| Driver (a typed workflow skill) | Runs in the main thread: can ask the user, spawns the agents, lasts the whole run | Everything it reads stays in its context and is re-read every turn, so it reads only what a script prints | `references/composition.md`, `references/skills.md` |
| Forked skill | Isolated context; the main thread gets a result, not the work | Cannot ask the user; gets no conversation history | `references/skills.md` |
| Agent | Fresh context, its own tool list, model and preloaded skills; runs many at once | Cannot ask the user; plugin agents ignore `hooks`, `mcpServers`, `permissionMode`, `initialPrompt` | `references/agents.md` |
| Hook | Deterministic; fires on lifecycle events whatever the model does | Session-wide for every session the plugin is enabled in; fails open unless it exits 2 | `references/hooks.md` |
| MCP server | Real tools with auth and state, usable by subagents | Starts with the plugin; output capped (25k tokens by default); tool names bind to server names | `references/mcp.md` |
| Script | Exact, free, repeatable; the only reader and writer of where a run stands | No judgment | `references/composition.md`, `references/skills.md` |
| Ledger | Outlives every context: a new chat resumes from it and an audit checks against it | A file format a script must parse; true only while a script is its one writer | `references/composition.md` |
| Manifest, `userConfig`, env vars | Per-user config, paths that survive install | Paths must stay inside the plugin root | `references/manifest.md` |

## Which reference to read

Read only the file for the component in front of you; each is self-contained.

| When you are… | Read |
|---|---|
| Designing a workflow or writing its driver: the loop, the ledger, the hooks that hold a run, what goes in an agent vs a skill, how skills attach to an agent | `references/composition.md` |
| Writing or reviewing a `SKILL.md` (frontmatter, invocation, description, layout, writing style) | `references/skills.md` |
| Writing or reviewing an `agents/*.md` | `references/agents.md` |
| Adding a hook, in `hooks/hooks.json` or in skill or agent frontmatter | `references/hooks.md` |
| Adding an MCP server | `references/mcp.md` |
| Editing `plugin.json`, adding `userConfig`, using a path variable, or anything about install and caching | `references/manifest.md` |
| Considering output styles, LSP, monitors, themes, workflows, commands, `bin/`, `settings.json` | `references/other.md` |
| Reviewing a design or a phase for what can fail without an error | `references/edge-cases.md` |
| Testing that a component loads, or proving a fact | the **How to test it** section at the end of that component's file |
