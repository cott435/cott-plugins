# Edge cases

Things that fail without an error, or work in a working copy and break once installed. Each
entry is: the symptom, the rule that prevents it, and where the fact comes from (the
component file that carries its evidence). Read this when reviewing a design, a phase note,
or a finished component. Add to it whenever an eval or an incident finds a new one, with
the log as the source.

## Silent no-ops

| Symptom | Rule | Source |
|---|---|---|
| An agent's hook never fires; its MCP server never starts; its `permissionMode` has no effect | Plugin agents ignore `hooks`, `mcpServers`, `permissionMode`, `initialPrompt`. Use plugin hooks and plugin MCP servers. `check-contracts`' `frontmatter` claim fails on them. | `agents.md` |
| Rules written in the plugin's `CLAUDE.md` are never followed | It is never loaded as plugin context. Put runtime rules in skills or agent files. | `manifest.md` |
| A hook matcher on an MCP server's name never fires | Match the full tool name, `mcp__plugin_<plugin>_<server>__<tool>`. | `hooks.md` |
| Only some of a plugin's commands load after adding a `commands` (or `agents`, `outputStyles`) key | Those keys replace the folder scan. List the default folder too. | `manifest.md` |
| A settings key in the plugin's `settings.json` does nothing | Only `agent` and `subagentStatusLine` take effect. | `other.md` |
| A trigger phrase at the end of a long description never matches | The listing truncates `description` + `when_to_use` at 1,536 characters. Put triggers first. | `skills.md` |
| A load check says a typed skill is missing | `claude -p` does not list `disable-model-invocation` skills; invoke it by name instead. | `skills.md` |

## Fails open

| Symptom | Rule | Source |
|---|---|---|
| A guard hook lets a forbidden call through | Only exit 2 blocks. A crash, a missing or non-executable script, a `PreToolUse` timeout, or malformed JSON with exit 0 lets the action proceed. Test each failure path. | `hooks.md` |
| A secret appears where it should not, or fails to appear where it should | Sensitive `userConfig` values are placeholders in skill and agent content, and shell-form hooks reject `${user_config.*}`. Pass secrets to hooks as `CLAUDE_PLUGIN_OPTION_<KEY>` or exec-form `args`, and to MCP servers through their config. | `manifest.md` |

## Works locally, breaks installed

| Symptom | Rule | Source |
|---|---|---|
| A skill cannot find a file it reads | Everything a component reads is inside the plugin root, reached through `${CLAUDE_PLUGIN_ROOT}`, never `..` or a sibling folder. | `manifest.md` |
| State is lost on every plugin update | Write state to `${CLAUDE_PLUGIN_DATA}`, never `${CLAUDE_PLUGIN_ROOT}`. | `manifest.md` |
| `$CLAUDE_PLUGIN_ROOT` is empty in a command the model runs | The variables are substituted in skill and agent bodies, not exported to Bash. Write `${CLAUDE_PLUGIN_ROOT}` in the body so the path is substituted on load. | `skills.md` |
| The plugin will not install on claude.ai or Cowork | Remove `bin/`. Remove any XML-style tag from skill descriptions. | `other.md`, `skills.md` |
| The desktop app stops listing the plugin | claude.ai rejects an XML-style tag in a skill description, and a second `plugin.json` anywhere in the tree ("Zip must contain exactly one plugin.json"). Ship fixture manifests renamed. | `skills.md`; `evals/2026-09-21-description-xml-tag-contract.md` and plugin-dev's CHANGELOG 0.9.3 |
| A plugin using `userConfig.options` does not load for some users | `options` needs Claude Code v2.1.271. | `manifest.md` |

## Context and concurrency

| Symptom | Rule | Source |
|---|---|---|
| An agent needs a user decision and stalls or guesses | Subagents and forked skills never get `AskUserQuestion`. Return the question; the workflow skill asks. | `agents.md` |
| A fan-out of 30 agents does not all start | Concurrency is limited (20 by default [unconfirmed]); batch the fan-out and say so in the design. | `agents.md` |
| A deep agent cannot delegate | Subagents nest three layers below the main conversation; at the limit there is no `Agent` tool. | `agents.md` |
| A wide fan-out uses far more context than expected | `skills:` preloads full content into every instance. Preload only what every run needs. | `composition.md` |
| An agent does not follow the project's `CLAUDE.md` | It loads its own `CLAUDE.md` hierarchy from its working directory, or none with `omitClaudeMd`. Put what it needs in its file or its skills. | `agents.md` |
| A plugin hook changes behavior in unrelated repos | Plugin hooks run in every session the plugin is enabled in. Scope the script by `cwd`. | `hooks.md` |

## Naming

| Symptom | Rule | Source |
|---|---|---|
| Renaming an MCP server breaks agents | Tool names include the server name; agents' `tools` lists and hook matchers name them. Hold them together with a contract. | `mcp.md` |
| Two skills with the same name | Which wins is [unconfirmed]. Avoid the collision; the plugin prefix keeps plugin skills apart from each other, not necessarily from project or user skills. | `skills.md` |
| An agent in a subfolder is not found by its short name | Subfolders of `agents/` add name segments (`my-plugin:review:security`). | `agents.md` |
| `claude plugin eval` picks up the wrong files | It treats any directory under `evals/` with `prompt.md` or `case.yaml` as a case. Keep its cases in their own eval directory. | `manifest.md` |
