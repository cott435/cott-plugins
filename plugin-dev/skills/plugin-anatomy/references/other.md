# The other components

**Sources:** https://code.claude.com/docs/en/plugins-reference.md (standard layout) ·
https://code.claude.com/docs/en/plugins/components.md. Read 2026-09-26 against Claude Code
2.1.270. Each of these is documented, but none has been used or load-tested in this repo
yet. The first plan that uses one proves it loads in its phase 0.

| Component | Location | What it is | Reach for it when | Watch for |
|---|---|---|---|---|
| Legacy commands | `commands/*.md` | flat Markdown commands; subfolders add name segments (`commands/db/migrate.md` → `/<plugin>:db:migrate`) [docs] | never for new work; a skill does everything a command does and supports `references/` | the manifest's `commands` key replaces the folder scan [docs] |
| Executables | `bin/` | files on the Bash tool's `PATH` while the plugin is enabled, so Claude runs them as bare commands [docs] | a script Claude runs often enough that a full `${CLAUDE_PLUGIN_ROOT}` path is noise | **claude.ai and Cowork do not install a plugin that has `bin/`** [docs]; for a plugin meant for them, keep scripts under `scripts/` and call them by path |
| Output styles | `output-styles/<name>.md` | changes how Claude formats and phrases replies; `name` and `description` frontmatter; listed in the output-style picker as `<plugin>:<name>` [docs] | the plugin's value is a way of answering, not a task | applies to the whole session once chosen |
| LSP servers | `.lsp.json` | language servers for code intelligence [docs] | a plugin for one language or file type | two servers claiming one extension: the first registered wins, with a warning in the plugin Errors tab [docs] |
| Monitors | `monitors/monitors.json`, or `experimental.monitors` | background processes [docs] | watching something for the session's lifetime | run only in interactive sessions; the manifest shape may still change; no `CLAUDE_PLUGIN_OPTION_<KEY>` in their environment [docs] |
| Themes | `themes/*.json`, or `experimental.themes` | color themes [docs] | rarely | the manifest shape may still change [docs] |
| Workflows | `workflows/*.js` | workflow orchestration scripts [docs] | a fixed multi-agent pipeline worth running as code rather than as a skill's instructions | new; prove it loads before a design depends on one |
| Plugin settings | `settings.json` (or the manifest's `settings`) | defaults applied while the plugin is enabled; only `agent` and `subagentStatusLine` take effect [docs] | the plugin should make one of its agents the main-session agent | any other key is silently ignored [docs] |
| Channels | the manifest's `channels` | message channels bound to one of the plugin's MCP servers [docs] | a bridge to a chat app | — |
