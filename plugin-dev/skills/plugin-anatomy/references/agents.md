# Agents

**Sources:** https://code.claude.com/docs/en/sub-agents.md ·
https://code.claude.com/docs/en/plugins/components.md (plugin agents). Read 2026-09-26
against Claude Code 2.1.270.

## Frontmatter

`check-contracts`' `frontmatter` check reads the block below. A key outside `allowed` fails
the sweep, and so does a key in `ignored_in_plugins`, because it looks as if it works and
does nothing.

<!-- frontmatter-keys: agent -->
```yaml
allowed: [name, description, tools, disallowedTools, model, permissionMode, maxTurns, skills,
          mcpServers, hooks, memory, background, omitClaudeMd, effort, isolation, color,
          initialPrompt, experimental]
ignored_in_plugins: [hooks, mcpServers, permissionMode, initialPrompt]
```

| Field | What it does |
|---|---|
| `name` | Unique identifier. [docs] |
| `description` | When Claude should delegate to this agent. [docs] |
| `tools` | Allowlist, as a comma-separated string or a YAML list. Omitted: the agent inherits the session's tools, minus the always-removed ones (below). [docs] |
| `disallowedTools` | Denylist, removed from the inherited or listed tools. [docs] |
| `model` | `sonnet`, `opus`, `haiku`, `fable`, a full model ID, or `inherit`. [docs] |
| `maxTurns` | Stops the agent after that many turns. [docs] |
| `skills` | Skills preloaded at startup. The **full content** is injected, not only the description. [docs] |
| `memory` | Persistent memory scope: `user`, `project` or `local`. [docs] |
| `background` | `true` keeps the agent in the background even when asked to run in the foreground. [docs] |
| `omitClaudeMd` | `true` launches without the user, project and local `CLAUDE.md` files. [docs] |
| `effort` | Effort level while active. [docs] |
| `isolation` | `worktree` runs the agent in a temporary git worktree. [docs] |
| `color` | Display color. [docs] |
| `experimental` | A map of experimental options. [docs] |
| `permissionMode`, `mcpServers`, `hooks`, `initialPrompt` | Work in project and user agents; **ignored for plugin agents**, for security. [docs: components, "Ignored fields"] |

## What a plugin agent gets

- **A fresh context.** Not the parent conversation. It loads its own `CLAUDE.md` hierarchy
  from its working directory unless `omitClaudeMd` is set. A plugin's own `CLAUDE.md` is
  never loaded as context for anyone. [docs] So rules an agent must follow go in the agent
  file or a skill it preloads, never in the plugin's `CLAUDE.md`.
- **No `AskUserQuestion`, ever.** It is removed from every subagent even when listed in
  `tools`. [docs] An agent that meets a decision it cannot make returns it as a question in
  its output, and the workflow skill that spawned it asks.
- **The `Agent` tool, down to a depth.** Subagents can spawn subagents up to three layers
  below the main conversation; at the limit the `Agent` tool is withheld and the agent does
  the work itself. [docs] The limit is the environment variable
  `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH`, inherited by child processes. A Claude Code cloud
  session (claude.ai/code, 2.1.285) sets it to `1`: its subagents have no `Agent` tool at
  all, and neither do the subagents of a `claude -p` started inside it, unless that child
  is started with the variable raised (`=3` gave a nested reply). [proven:
  evals/2026-09-29-run-phases.md] A design that needs a subagent to delegate checks it
  first. Default concurrency is 20 running subagents
  (`CLAUDE_CODE_MAX_CONCURRENT_SUBAGENTS`) [unconfirmed: from a docs summary, not re-read].
- **Skills.** Preloaded ones (full content) plus any skill it invokes through the `Skill`
  tool, which it may do for unlisted plugin, project and user skills when `Skill` is in its
  tools. [docs]
- **MCP tools** from the session's servers, filtered by `tools`/`disallowedTools`. It cannot
  declare its own servers (ignored field above); a server it needs is a plugin MCP server.
  [docs]
- **No plugin path variables in Bash.** `${CLAUDE_PLUGIN_ROOT}` is substituted in the agent
  file's Markdown body when it loads, but it is not in the environment of the agent's Bash
  commands. [docs]
- **What reaches its caller.** With a `SubagentHandback` tool in its session, the caller
  receives the message of the agent's **last hand-back**, not its last turn: the Agent tool's
  result says the report "was delivered … as a message" and repeats nothing. An agent that
  hands back and then keeps working (a stop hook sent it back, say) must hand back again, or
  the caller acts on the stale report. A `SubagentStop` hook that exits 0 ends the agent with
  no further turn, so its stderr never reaches the agent. [proven:
  dev-team/evals/2026-09-28-audit-run-package-1493ed56.md, 9 of 9 implementer runs, Claude
  Code 2.1.281 in the desktop app; a CLI session without the tool is unconfirmed]
- **Its scoped name** is `<plugin>:<file>`; subfolders of `agents/` add segments
  (`agents/review/security.md` → `my-plugin:review:security`). [docs]

## The description

- Say when to delegate, concretely, so the parent picks this agent over a general one.
- The Cowork plugin guide recommends `<example>` blocks in agent descriptions. claude.ai
  rejects XML-style tags in *skill* descriptions [proven:
  evals/2026-09-21-description-xml-tag-contract.md]; whether it also rejects them in *agent*
  descriptions is [unconfirmed]. Until an eval settles it, this repo's contract forbids them
  in both.

## How to test it

| What | How | Kind |
|---|---|---|
| Frontmatter keys are real and none is silently ignored | `check-contracts`' `frontmatter` claim | mechanical |
| It registers | `/reload-plugins` then `/agents` in an interactive session, or `claude --plugin-dir <plugin> -p "List the agents you have from <plugin>"` | load |
| It does the job | `run-evals` behavioral loop. Note that a general-purpose subagent given the agent file as instructions does not reproduce its `tools:` or `skills:`; the log says "proxy" | behavioral |
