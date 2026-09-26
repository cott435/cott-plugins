# Hooks

**Sources:** https://code.claude.com/docs/en/hooks.md ·
https://code.claude.com/docs/en/plugins-reference.md (environment variables, userConfig).
Read 2026-09-26 against Claude Code 2.1.270.

## Where hooks come from

| Defined in | Active | Notes |
|---|---|---|
| `hooks/hooks.json`, or the manifest's `hooks` key (both load and merge) | every session the plugin is enabled in, from session start | merges with the user's and project's hooks; none replaces another [docs] |
| A skill's `hooks:` frontmatter | from the skill's invocation to the end of the session; `once: true` removes it after its first successful run | [docs] |
| An agent's `hooks:` frontmatter | only while that agent runs; `Stop` becomes `SubagentStop` | **ignored for plugin agents** [docs] |

`hooks/hooks.json` has the settings-file shape, plus an optional top-level `description`:

```json
{
  "description": "What these hooks are for",
  "hooks": {
    "PostToolUse": [
      {
        "matcher": "Write|Edit",
        "hooks": [
          { "type": "command", "command": "${CLAUDE_PLUGIN_ROOT}/scripts/format.sh",
            "args": [], "timeout": 30 }
        ]
      }
    ]
  }
}
```

## Events

`SessionStart`, `Setup`, `UserPromptSubmit`, `UserPromptExpansion`, `PreToolUse`,
`PermissionRequest`, `PermissionDenied`, `PostToolUse`, `PostToolUseFailure`,
`PostToolBatch`, `Notification`, `MessageDisplay`, `SubagentStart`, `SubagentStop`,
`TaskCreated`, `TaskCompleted`, `Stop`, `StopFailure`, `TeammateIdle`, `InstructionsLoaded`,
`ConfigChange`, `CwdChanged`, `DirectoryAdded`, `FileChanged`, `WorktreeCreate`,
`WorktreeRemove`, `PreCompact`, `PostCompact`, `PreModelSwitch`, `PostModelSwitch`,
`Elicitation`, `ElicitationResult`, `SessionEnd`. [docs]

The ones plugins use most:

| Event | Use for | Can block? |
|---|---|---|
| `PreToolUse` | refusing a tool call (a write outside a folder, a forbidden command) | yes, exit 2 |
| `PostToolUse` | formatting or validating after an edit; adding context about what just happened | no |
| `UserPromptSubmit` | injecting context for a prompt; refusing a prompt | yes, exit 2 (erases the prompt) |
| `SessionStart` | loading context once per session (matchers `startup`, `resume`, `clear`, `compact`, `fork`) | no |
| `Stop` / `SubagentStop` | refusing to stop until a check passes (tests green, file written) | `Stop`: yes, exit 2 continues the conversation |

## Handler types and timeouts

| Type | Runs | Default timeout |
|---|---|---|
| `command` | a shell command, JSON on stdin | 600s (30s on `UserPromptSubmit`, model-switch events; 10s on `MessageDisplay`) |
| `http` | a POST | same as `command` |
| `mcp_tool` | an MCP tool call | same as `command` |
| `prompt` | a prompt to a model | 30s |
| `agent` | a subagent | 60s |

`SessionEnd` hooks share a 1.5s budget, raised to match a longer per-hook timeout up to 60s.
[docs] Prefer `command` for anything that can be decided by code: it is exact and free.

## Exit codes

- **0**: success. JSON on stdout (starting `{`, ending `}`) is read as structured output;
  plain stdout is added as context on `UserPromptSubmit`, `UserPromptExpansion`,
  `SessionStart` and `PostModelSwitch`. [docs]
- **2**: blocks, on events that can block, even if the JSON says `allow`. The reason is the
  JSON's, or stderr. [docs]
- **Anything else**: a non-blocking error; the action proceeds. The exceptions are
  `WorktreeCreate` and `WorktreeRemove`, which fail on any nonzero exit. [docs]

So a guard **fails open**. If it crashes, is not executable (exit 127), times out on
`PreToolUse`, or prints malformed JSON with exit 0, the tool call goes ahead. [docs] A guard
that matters exits 2 explicitly on every path that should block, and is tested for the
failure cases too.

## Matchers

- `*`, empty or omitted: everything. Letters, digits, `_`, `-`, spaces, `,` and `|` only:
  exact names or a list (`Edit|Write`). Any other character makes it an unanchored JavaScript
  regex. [docs]
- A plugin's own MCP tools are `mcp__plugin_<plugin>_<server>__<tool>`, hyphens kept
  (`mcp__plugin_my-plugin_db__query`). A matcher on the server name alone never fires. [docs]
- `SubagentStart`/`SubagentStop` match on agent type, such as `^my-plugin:reviewer$`. [docs]
- Every event's input carries `cwd`, `session_id`, `transcript_path`, `permission_mode`,
  `hook_event_name`, and inside a subagent `agent_id` and `agent_type`. [docs]

## Scope it

A plugin hook runs in **every** session the plugin is enabled in, including repos that have
nothing to do with the plugin. [docs] Check `cwd` (or a marker file in it) first and exit 0
when the hook does not apply. This is the hook equivalent of a skill description's scoping
clause.

## Paths and config

- In `command` and `args`, `${CLAUDE_PLUGIN_ROOT}`, `${CLAUDE_PLUGIN_DATA}` and
  `${CLAUDE_PROJECT_DIR}` are substituted, and all three are exported to the process with
  `CLAUDE_PLUGIN_OPTION_<KEY>` for each `userConfig` option. [docs]
- Prefer exec form (`command` + `args`) so a path with spaces stays one argument. In shell
  form, quote it: `"\"${CLAUDE_PLUGIN_ROOT}\"/scripts/x.sh"`. [docs]
- Shell-form commands reject `${user_config.*}`; use exec-form `args` or read
  `CLAUDE_PLUGIN_OPTION_<KEY>`. [docs]
- Scripts a hook runs live in the plugin (a `scripts/` folder), never outside the plugin root.

## How to test it

| What | How | Kind |
|---|---|---|
| The script decides correctly | pipe a recorded event JSON into it and check the exit code and stdout, once per path, including a malformed input | mechanical |
| It is registered | `/hooks` in an interactive session with the plugin loaded | load |
| It fires in a real session, and only where scoped | a session that triggers the event inside scope and one outside; the transcript shows the hook's effect in the first only | behavioral |
