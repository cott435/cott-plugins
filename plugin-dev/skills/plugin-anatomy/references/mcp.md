# MCP servers

**Sources:** https://code.claude.com/docs/en/plugins/components.md ·
https://code.claude.com/docs/en/plugins-reference.md · https://code.claude.com/docs/en/mcp.md.
Read 2026-09-26 against Claude Code 2.1.270.

## When a server is worth it

A plugin MCP server starts with the plugin and gives Claude real tools with auth and state.
[docs] It is the right component when the plugin needs an authenticated API, a database, or a
stateful session. It is the wrong one when:

- WebFetch or WebSearch reaches the data (public pages, open APIs without keys);
- a script in `scripts/` can call the API once and write a file, the usual case for a batch
  job that a workflow skill runs;
- the user already has a server for the service; point to it instead of shipping a second.

## Defining one

`.mcp.json` at the plugin root, or the manifest's `mcpServers` key. Both load, and a server
name declared in the manifest replaces the same name in `.mcp.json`. [docs]

```json
{
  "mcpServers": {
    "db": {
      "command": "${CLAUDE_PLUGIN_ROOT}/servers/db-server",
      "args": ["--config", "${CLAUDE_PLUGIN_ROOT}/config.json"],
      "env": { "DB_URL": "${user_config.db_url}" }
    }
  }
}
```

- Transports: `stdio` (a local process), and `http`, `sse`, `ws` (remote). The manifest also
  accepts `.mcpb`/`.dxt` bundles and an `https://` bundle URL. [docs]
- `${…}` resolves in `command`, `args` and `env` for stdio servers, which also receive
  `CLAUDE_PLUGIN_ROOT` and `CLAUDE_PLUGIN_DATA` in their environment. For remote servers it
  resolves in `url`, `headers` and `headersHelper`. [docs]
- `${user_config.KEY}` is substituted in MCP config. [docs] A `headersHelper` script gets no
  option values in its environment and must obtain a secret itself. [docs]
- A server's installed dependencies (such as `node_modules`) go in `${CLAUDE_PLUGIN_DATA}`,
  which survives updates, not in the plugin root, which does not. [docs]

## Tool names

A plugin server's tools are named `mcp__plugin_<plugin>_<server>__<tool>`, hyphens kept:
`mcp__plugin_my-plugin_db__query`. That full name is what goes in permission rules, hook
matchers, and agents' `tools` lists. [docs] So a server's name is an interface: renaming it
breaks every `tools:` entry and matcher that names its tools, and a `forbid` or
`names_listed` claim in `contracts.yml` should hold them together.

## Agents and servers

Subagents can use the session's MCP tools, subject to their `tools`/`disallowedTools`.
[docs] A plugin agent cannot declare a server of its own; `mcpServers` in its frontmatter is
ignored. [docs] Every server a plugin's agents need is a plugin server.

## Limits

- Tool output is capped at 25,000 tokens by default (`MAX_MCP_OUTPUT_TOKENS`).
  [unconfirmed: from a docs summary, not re-read] A tool that can return more pages its
  results.
- On reload, an unchanged server keeps its connection, a changed one reconnects, and a
  removed one disconnects. [unconfirmed: from a docs summary, not re-read]

## How to test it

| What | How | Kind |
|---|---|---|
| The config is valid | `claude plugin validate`; whether it checks `.mcp.json` itself, and from which version, is [unconfirmed], so also check at load | mechanical |
| The server starts and its tools appear | `/mcp` in an interactive session with the plugin loaded; each tool is listed under its full name | load |
| A skill uses it correctly without the real service | `claude plugin eval` can answer MCP calls from mocks under `evals/mocks/<server>/<tool>.md` (see `manifest.md` on the eval directory) | behavioral |
