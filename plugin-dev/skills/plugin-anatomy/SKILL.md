---
name: plugin-anatomy
description: The source of truth for what each Claude Code plugin component is for and exactly how it behaves - skills, agents, hooks, MCP servers, the manifest, and the rarer ones - with the routing rules for which component a responsibility belongs in, how skills and agents combine, and the edge cases that fail silently. Every fact carries its source and whether it is documented, proven by an eval, or unconfirmed. Use when designing or planning a plugin, deciding whether something should be a skill, agent, hook, MCP server or script, writing or reviewing frontmatter, hooks.json, .mcp.json or plugin.json, or when a platform fact about plugins is in question. Use only inside a plugin's own subdirectory (one containing .claude-plugin/plugin.json) or the marketplace repo that holds it.
---

# Plugin anatomy

This skill is the one place a plugin-dev skill, or a person building a plugin, looks up what
a component can do. `design-plugin` routes responsibilities with it, `plan-phases` copies
frontmatter from it, `run-phase` reads it before creating a component, and `check-contracts`
reads its allowed-key lists. A fact stated anywhere else in plugin-dev cites the file here
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

## Routing: which component a responsibility belongs in

Ask these questions in order about each responsibility a design has. The first *yes* is
usually the answer.

1. **Must it happen every time, whatever the model decides?** A block, a guard, a format
   step after every edit, context injected at session start. → **hook**. Only a hook is
   deterministic; an instruction in a skill is a request the model can miss.
2. **Is it a deterministic transform** (count, filter, validate, convert, fetch a list)?
   → **script**, in the skill's `scripts/`, or in the plugin's `bin/` when Claude should run
   it as a bare command (but `bin/` blocks installation on claude.ai and Cowork).
3. **Does it talk to an external system that has auth or state?** → **MCP server**, when
   WebFetch or a script calling the API cannot do it cleanly.
4. **Does it need the user partway through**, to answer a question or approve something?
   → it runs in the **main thread**: a **workflow skill** (inline, not forked). Subagents,
   and therefore forked skills, never get `AskUserQuestion`.
5. **Is it a way of working done repeatedly, in parallel, or in a context kept clean of the
   rest?** → **agent**, spawned by a workflow skill.
6. **Is it a self-contained procedure the user starts, that returns a result without
   asking anything?** → **skill with `context: fork`**, keeping the work out of the main
   context.
7. **Is it knowledge** (a method, a template, a checklist, a style) needed when a topic comes
   up, or by more than one agent? → **knowledge skill**, model-invoked or preloaded by agents.
8. **Is it a per-user setting** (an endpoint, a token, a default)? → **`userConfig`** in
   `plugin.json`.
9. **Is it state that must outlive a session?** → `${CLAUDE_PLUGIN_DATA}`, or files in the
   user's project. Never under `${CLAUDE_PLUGIN_ROOT}`, which is replaced on every update.

Rarer components (output styles, LSP servers, monitors, themes, workflows, legacy commands,
the plugin `settings.json`) are in `references/other.md`. Reach for one only when a design
names the need it exists for.

## Components at a glance

| Component | Strength | Costs and limits | Read |
|---|---|---|---|
| Knowledge skill | Name and description are the only context cost until it is used; references load on demand | Triggering is probabilistic; the listing truncates `description` + `when_to_use` at 1,536 characters | `references/skills.md` |
| Workflow skill (typed) | Runs in the main thread: sees the conversation, can ask the user, can spawn agents | Everything it reads stays in the main context | `references/skills.md` |
| Forked skill | Isolated context; the main thread gets a result, not the work | Cannot ask the user; gets no conversation history | `references/skills.md` |
| Agent | Fresh context, its own tool list, model and preloaded skills; runs many at once | Cannot ask the user; plugin agents ignore `hooks`, `mcpServers`, `permissionMode`, `initialPrompt` | `references/agents.md` |
| Hook | Deterministic; fires on lifecycle events whatever the model does | Session-wide for every session the plugin is enabled in; fails open unless it exits 2 | `references/hooks.md` |
| MCP server | Real tools with auth and state, usable by subagents | Starts with the plugin; output capped (25k tokens by default); tool names bind to server names | `references/mcp.md` |
| Script | Exact, free, repeatable | No judgment | `references/skills.md` |
| Manifest, `userConfig`, env vars | Per-user config, paths that survive install | Paths must stay inside the plugin root | `references/manifest.md` |

## Which reference to read

Read only the file for the component in front of you; each is self-contained.

| When you are… | Read |
|---|---|
| Deciding what goes in an agent vs a skill, or how several skills attach to one agent | `references/composition.md` |
| Writing or reviewing a `SKILL.md` (frontmatter, invocation, description, layout, writing style) | `references/skills.md` |
| Writing or reviewing an `agents/*.md` | `references/agents.md` |
| Adding a hook, in `hooks/hooks.json` or in skill or agent frontmatter | `references/hooks.md` |
| Adding an MCP server | `references/mcp.md` |
| Editing `plugin.json`, adding `userConfig`, using a path variable, or anything about install and caching | `references/manifest.md` |
| Considering output styles, LSP, monitors, themes, workflows, commands, `bin/`, `settings.json` | `references/other.md` |
| Reviewing a design or a phase for what can fail without an error | `references/edge-cases.md` |
| Testing that a component loads, or proving a fact | the **How to test it** section at the end of that component's file |
