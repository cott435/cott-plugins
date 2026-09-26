# The manifest, config, paths and install

**Sources:** https://code.claude.com/docs/en/plugins-reference.md (manifest reference) ·
https://code.claude.com/docs/en/plugin-evals.md (eval directory). Read 2026-09-26 against
Claude Code 2.1.270.

## `plugin.json`

At `.claude-plugin/plugin.json`. Only `name` is required (kebab-case; every component is
namespaced under it). [docs]

| Field | Notes |
|---|---|
| `name`, `displayName`, `version`, `description`, `author` (`name` required, `email`, `url`), `homepage` (must parse as a URL or the plugin fails to load), `repository`, `license`, `keywords` | metadata [docs] |
| `metadata` | free-form; Claude Code does not read it [docs] |
| `defaultEnabled` | default `true` [docs] |
| `dependencies` | plugins that must be enabled for this one to work [docs] |
| `settings` | only `agent` and `subagentStatusLine` take effect [docs] |
| `userConfig` | values prompted for when the plugin is enabled (below) [docs] |
| `channels` | message channels bound to the plugin's MCP servers [docs] |
| `skills` | extra skill directories; **adds to** the `skills/` scan; `"./"` names the root [docs] |
| `commands`, `agents`, `outputStyles`, `workflows`, `experimental.themes`, `experimental.monitors` | **replace** the default folder's scan; list the default folder too to keep it [docs] |
| `hooks`, `mcpServers`, `lspServers` | **merge** with the default file; a later same-named server replaces the earlier [docs] |
| `experimental.evals` | the directory `claude plugin eval` reads, when not `evals/` [docs] |

`version`: setting it keeps users on that version until it changes. [docs] In this repo,
`bump-version` owns it and the marketplace row together.

## Path rules

- Every component path starts with `./` and resolves inside the plugin root. A path with
  `..`, or one that resolves outside, does not load (`path escapes plugin directory`). A
  missing path does not load either. [docs]
- Setting a key that replaces a default folder while the folder also exists loads only the
  manifest's paths, with the warning `Default <folder>/ folder is ignored…`. [docs]
- An installed plugin runs from a versioned cache directory, and `${CLAUDE_PLUGIN_ROOT}`
  moves on every update. [docs] Anything a component reads must be inside the plugin; a
  reference to a sibling directory works from a working copy and breaks once installed.
- Whether symlinks inside a plugin survive install is [unconfirmed]; do not rely on them.

## Path variables

| Variable | Resolves to | Use for |
|---|---|---|
| `${CLAUDE_PLUGIN_ROOT}` | the installed version's directory | reading bundled scripts, templates, config. Never write there |
| `${CLAUDE_PLUGIN_DATA}` | `~/.claude/plugins/data/<id>/`, kept across updates, deleted on final uninstall unless `--keep-data` | installed dependencies, caches, generated files |
| `${CLAUDE_PROJECT_DIR}` | the project root | project-local files |

Where they resolve [docs]:

| Component | Substituted in | Exported to the process |
|---|---|---|
| Hook commands | `command`, `args` | all three, plus `CLAUDE_PLUGIN_OPTION_<KEY>` |
| MCP stdio servers | `command`, `args`, `env` | `CLAUDE_PLUGIN_ROOT`, `CLAUDE_PLUGIN_DATA` |
| MCP remote servers | `url`, `headers`, `headersHelper` | n/a |
| LSP servers | `command`, `args`, `env`, `workspaceFolder` | all three |
| Monitor commands | `command` | not exported |
| Skill, command and agent Markdown | anywhere in the body | n/a |

None of them is in the environment of Bash commands the model runs, in the main session or
in a subagent. Write the `${…}` in the skill or agent body, where it is substituted on load.
[docs]

## `userConfig`

Each key (letters, digits, `_`, not starting with a digit) is a strict object: `type`
(`string`, `number`, `boolean`, `directory`, `file`), `title`, `description`, and optionally
`required`, `default`, `options` (a picker; needs v2.1.271, and a plugin declaring it will
not load on earlier versions), `multiple`, `sensitive`, `min`/`max`. An unknown key fails
validation. [docs]

- Non-sensitive values are stored in the user's `settings.json` under `pluginConfigs`;
  `sensitive: true` masks input and stores the value in the platform's credential store.
  [docs]
- `${user_config.KEY}` is substituted in MCP and LSP config, exec-form hook `args`, and skill
  and agent content. In skill and agent content only non-sensitive values are substituted; a
  sensitive one becomes a placeholder, so a secret never enters the model's context this way.
  [docs]
- Hooks get every option as `CLAUDE_PLUGIN_OPTION_<KEY>`. Shell-form hook commands, monitor
  commands and MCP `headersHelper` reject `${user_config.*}`. [docs]

## The eval directory

`claude plugin eval` treats every directory under `evals/` that contains a `prompt.md` or a
`case.yaml` as a case, and writes `evals/results/<timestamp>/`. [docs] This repo's `evals/`
holds logs, `sets/`, `fixtures/` and the gitignored `workspace/`, none of which contains
those files, so the two coexist. If a plugin here adopts `claude plugin eval`, set
`experimental.evals` (or pass `--eval-dir`) to a separate directory rather than mixing its
cases in with `run-evals`' sets.

## `CLAUDE.md` in a plugin

Claude Code does not load a `CLAUDE.md` at the plugin root; `claude plugin validate` warns
about it. [docs] In this repo each plugin's `CLAUDE.md` is for people and sessions working
*on* the plugin's source. Instructions the plugin gives at runtime go in skills.

## How to test it

| What | How | Kind |
|---|---|---|
| Manifest, paths and `userConfig` schema | `claude plugin validate <plugin>` | mechanical |
| It installs from the marketplace, not only from a working copy | install it from the marketplace in a scratch project and run one skill that reads a bundled file | load |
