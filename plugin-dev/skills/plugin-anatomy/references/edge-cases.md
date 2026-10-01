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
| A subagent that should delegate does the work itself, or stops for want of an `Agent` tool | `CLAUDE_CODE_MAX_SUBAGENT_SPAWN_DEPTH` caps nesting; cloud sessions set `1`. Check it before relying on a subagent that spawns. | `agents.md` |
| Resuming a headless child session reaches the wrong conversation | Inside a cloud session every `claude -p` child reports the parent's session id. Give each child its own `--session-id <uuid>`, and `--resume` that id. [proven: evals/2026-09-29-run-phases.md] | `edge-cases.md` |

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
| A fan-out of 30 agents does not all start | At most 20 subagents run at once. The 21st spawn fails ("Concurrent subagent limit reached. You can run 20 subagents at once.") and is not queued. Batch the fan-out, start the rest as slots free, and say so in the design. | `agents.md` |
| A caller acts on an agent's `done` although the agent went on and ended blocked | With `SubagentHandback`, only the agent's first hand-back reaches its caller; a second call is refused and later text reaches nobody. Hand back only when nothing after it can change the answer, or carry the outcome in a file the caller reads. | `agents.md` |
| A hook inside a subagent finds none of the agent's own records in `transcript_path` | That path is the parent session's. The subagent's transcript is `<transcript_path minus .jsonl>/subagents/agent-<agent_id>.jsonl`; `SubagentStop` also gives it as `agent_transcript_path`. | `hooks.md` |
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
| A subagent cannot write `analysis.md`, `REPORT.md`, `summary-2026.md` or `findings.md` | Claude Code refuses a subagent's Write of any `.md` whose file name starts `analysis`, `report`, `summary` or `findings`, in any case and in any directory. Give a file an agent must write another name: `docs/api/<pkg>/index.md`, not `docs/api/analysis.md`. Whether Edit or a shell write is refused too is [unconfirmed]. [proven: dev-team/evals/2026-09-28-remake-phase11-bundle.md, Claude Code 2.1.270; dev-team/evals/2026-09-30-2.2-run-fixes.md, `docs/api/analysis.md`] | `edge-cases.md` |
| A headless run is on an older model than the alias suggests | `claude -p --model sonnet` was Sonnet 5 in CLI 2.1.283 while the Agent tool's `sonnet` was Sonnet 5.5. Pass the full model ID and check the transcript's `model`. | `agents.md` |
| `claude plugin eval` picks up the wrong files | It treats any directory under `evals/` with `prompt.md` or `case.yaml` as a case. Keep its cases in their own eval directory. | `manifest.md` |
