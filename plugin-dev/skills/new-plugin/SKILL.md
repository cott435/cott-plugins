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
- Whether it has agents, commands, or only skills

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
