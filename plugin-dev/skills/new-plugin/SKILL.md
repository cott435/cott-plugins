---
name: new-plugin
description: Scaffold a new Claude Code plugin as a subdirectory of this marketplace repo — manifest, README, CLAUDE.md, versioning and eval scaffolding, site config — and register it in marketplace.json. Use when starting a new plugin from scratch, or when converting a loose folder of agents and skills into a proper plugin.
argument-hint: "<plugin-name> [one-line description]"
---

# Starting a new plugin

Every plugin is a subdirectory of this repo (`cott-plugins`), with an entry in
`.claude-plugin/marketplace.json` pointing at it by relative path. There is no separate repo
or remote to set up — that is the whole appeal of the bundled layout.

## Ask first, if it is not already clear

- The plugin's name (kebab-case; it becomes the directory name and the `/<name>:` command
  prefix)
- One line on what it does
- Which components it has: skills, agents, hooks, MCP servers. `plugin-anatomy`'s routing
  guide says which a responsibility belongs in; commands are legacy and new plugins use skills

## Scaffold

From the repo root, create `<name>/` and copy the templates from this plugin:

```
mkdir -p <name>/{.claude-plugin,agents,skills,evals} <name>/site/{workflows,notes}
cp "${CLAUDE_PLUGIN_ROOT}/templates/.gitignore"       <name>/.gitignore
cp "${CLAUDE_PLUGIN_ROOT}/templates/CLAUDE.md"        <name>/CLAUDE.md
cp "${CLAUDE_PLUGIN_ROOT}/templates/VERSIONING.md"    <name>/VERSIONING.md
cp "${CLAUDE_PLUGIN_ROOT}/templates/CHANGELOG.md"     <name>/CHANGELOG.md
cp "${CLAUDE_PLUGIN_ROOT}/templates/evals/README.md"  <name>/evals/README.md
cp "${CLAUDE_PLUGIN_ROOT}/templates/site/site.yml"    <name>/site/site.yml
cp "${CLAUDE_PLUGIN_ROOT}/templates/README.md"        <name>/README.md
touch <name>/site/notes/.gitkeep
```

Remove `agents/` if the plugin has no agents yet; a component folder exists only for a
component the plugin ships. Hooks go in `<name>/hooks/hooks.json` and MCP servers in
`<name>/.mcp.json`, each in the shape its `plugin-anatomy` reference gives, when the first one
is added, not in the scaffold.

Then replace every `<name>` / `<description>` placeholder in the copied files, and write
`<name>/.claude-plugin/plugin.json`:

```json
{
    "name": "<name>",
    "description": "<one line>",
    "version": "0.1.0",
    "author": { "name": "Connor Ott" }
}
```

Do **not** write a `marketplace.json` inside `<name>/`. There is exactly one, at the repo
root, and it lists every plugin including this new one.

## Register it

Add a row to the root `.claude-plugin/marketplace.json`:

```json
{ "name": "<name>", "source": "./<name>", "description": "<one line>", "version": "0.1.0" }
```

Commit (the scaffold and the marketplace entry together), push, and on each machine that
wants it: `git pull`, then `/plugin marketplace update cott-plugins`, then
`/plugin install <name>@cott-plugins`.

## Then

Build the site to confirm the scaffold is discoverable
(`python3 "${CLAUDE_PLUGIN_ROOT}/scripts/build_site.py" <name>`). A zero-config plugin builds
fine: `site.yml` only controls reading order, and every key in it is optional.

A plugin that will have agents, or more than a couple of skills, is not written in the same
chat as its scaffold: `design-plugin --new <name>` runs this skill's steps once its design is
approved, commits the design beside the scaffold, and `plan-phases` then splits it into phases
that `run-phase` builds, one chat per phase. If that is the plugin being started, stop after
the scaffold and let `design-plugin` continue.
