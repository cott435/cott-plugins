# Skills

**Sources:** https://code.claude.com/docs/en/skills.md ·
https://code.claude.com/docs/en/plugins-reference.md (environment variables) ·
skill-creator's *Skill Writing Guide* (layout and style). Read 2026-09-26 against Claude Code
2.1.270.

## Contents

- Layout and progressive disclosure
- Frontmatter
- Invocation modes
- Substitutions
- Descriptions
- Writing the body
- How to test it

## Layout and progressive disclosure

```
skill-name/
├── SKILL.md          required: frontmatter + instructions
├── references/       loaded into context when SKILL.md says to read them
├── scripts/          executed, never loaded: deterministic or repetitive work
└── assets/           used in output: templates, icons, fonts
```

A skill loads in three levels: its name and description are always in context; the
`SKILL.md` body loads when the skill is invoked; bundled files load only when the body
points to them, and scripts run without loading at all. [docs] Keep the levels doing their
jobs:

- Keep `SKILL.md` under 500 lines. Past that, add a level: move detail into `references/`,
  and say in the body *when* to read each file, not only that it exists.
- A reference over 300 lines opens with a table of contents.
- When a skill covers several variants (clouds, frameworks, component kinds), put one
  reference per variant and a selection step in `SKILL.md`, so only the relevant file is
  read. This skill is laid out that way.
- A template used by one skill goes in that skill's `assets/`. A template several skills
  share goes in the plugin's root `templates/`, and each skill names it with
  `${CLAUDE_PLUGIN_ROOT}/templates/…`.
- A file one skill needs from another skill is reached through
  `${CLAUDE_PLUGIN_ROOT}/skills/<other>/…`, never a relative path: the working directory is
  the user's project, not the skill. [docs]

## Frontmatter

Every field the docs define. `check-contracts`' `frontmatter` check reads the block below,
so a key not listed here fails the sweep.

<!-- frontmatter-keys: skill -->
```yaml
allowed: [name, description, when_to_use, argument-hint, arguments, disable-model-invocation,
          user-invocable, allowed-tools, disallowed-tools, model, effort, context, agent,
          background, hooks, paths, shell, metadata, license, compatibility]
ignored_in_plugins: []
```

| Field | What it does |
|---|---|
| `name` | Command name in the `/` menu; defaults to the directory name. In a plugin it replaces the directory segment only, and the `<plugin>:` prefix stays. [docs] |
| `description` | What the skill does and when to use it; the model decides to invoke from this. [docs] |
| `when_to_use` | Extra trigger context (phrases, example requests), counted with `description` toward the listing limit. [docs] |
| `argument-hint` | Autocomplete hint for the arguments. [docs] |
| `arguments` | Named positional arguments, substituted as `$name`. [docs] |
| `disable-model-invocation` | `true`: only a person can start it. Its description is then **not** in the model's context at all. [docs] |
| `user-invocable` | `false`: only the model can invoke it; hidden from the `/` menu. [docs] |
| `allowed-tools` | Tools usable without a permission prompt during the invoking turn, such as `Bash(git *) Read`. [docs] |
| `disallowed-tools` | Tools removed while the skill is active. [docs] |
| `model`, `effort` | Model and effort while the skill is active. [docs] |
| `context` | `fork` runs the skill in a forked subagent context instead of inline. [docs] |
| `agent` | The subagent type a forked skill runs as; default `general-purpose`. [docs] |
| `background` | For a forked skill, `false` waits for its result. [docs] |
| `hooks` | Hooks registered when the skill is invoked, which stay for the rest of the session; `once: true` removes one after its first successful run. See `hooks.md`. [docs] |
| `paths` | Glob patterns that limit when the skill activates. [docs] |
| `shell` | The shell for `` !`command` `` preprocessing. [docs] |
| `metadata`, `license`, `compatibility` | Free-form data, an SPDX license, environment requirements. [docs] |

## Invocation modes

| Mode | Frontmatter | Who starts it | Description in context | Use for |
|---|---|---|---|---|
| Knowledge / automatic | (default) | the model, or a person | yes | methods, checklists, references the model should pull in when relevant |
| Typed only | `disable-model-invocation: true` | a person | no | workflows with side effects: commits, publishing, anything a person should decide to start |
| Model only | `user-invocable: false` | the model | yes | background knowledge nobody would type, often preloaded by agents |
| Forked | `context: fork` (+ `agent`) | either | per the above | a self-contained job whose work should not fill the main context |

- A forked skill's body becomes the subagent's task. It gets no conversation history, and it
  runs as a subagent, so it cannot use `AskUserQuestion`. [docs: sub-agents, "Available
  tools"] Anything that needs the user stays inline.
- `claude -p` does not list skills with `disable-model-invocation: true`, although they can
  still be invoked by name. A load check that asks `claude -p` to list skills will not show
  them. [proven: evals/2026-09-20-release-checks-0.9.0.md]
- Plugin skills are namespaced `/<plugin>:<skill>`. [docs] Two skills with the same name
  from different sources: which one wins is [unconfirmed]; avoid the collision.

## Substitutions

In the Markdown body [docs]:

- `$ARGUMENTS`, `$0`…`$N`, `$name` (from `arguments`).
- `${CLAUDE_SKILL_DIR}`: this skill's directory. `${CLAUDE_SESSION_ID}`,
  `${CLAUDE_PROJECT_DIR}`.
- In a plugin skill, `${CLAUDE_PLUGIN_ROOT}` and `${CLAUDE_PLUGIN_DATA}` are substituted in
  the body and in Bash rules in `allowed-tools`. They are **not** in the environment of Bash
  commands the model runs, so write `python3 "${CLAUDE_PLUGIN_ROOT}/scripts/x.py"` in the
  body (substituted when loaded), not `$CLAUDE_PLUGIN_ROOT` inside a script the model runs.
  [docs: plugins-reference, "Where each variable resolves"]
- `${user_config.KEY}` for non-sensitive values; a sensitive one becomes a placeholder. [docs]
- `` !`command` ``: runs before the skill loads and inlines the output. A failing command
  aborts the invocation. [docs]

## Descriptions

- The listing truncates `description` + `when_to_use` at 1,536 characters combined. Put
  what triggers the skill first. [docs]
- Say *when*, with the phrases a user would actually type, in third person. The body says
  *how*; do not repeat it in the description.
- A description must contain no XML-style tag such as `<name>`: claude.ai rejects the whole
  plugin for one, and the desktop app then stops listing it. Write placeholders as `{name}`.
  [proven: evals/2026-09-21-description-xml-tag-contract.md]
- A plugin installed everywhere (as plugin-dev is) scopes each model-invoked description to
  where it applies ("only inside a plugin's own subdirectory"), and its trigger set includes
  the same task outside that scope as should-not-trigger queries.

## Writing the body

- Instructions for the model, in the imperative, each important rule with its reason. A
  reason generalizes to cases the rule did not name; a bare MUST does not.
- Define output formats with the exact template, and give an example where a format is easy
  to get subtly wrong.
- Nothing stated in two files. Point to the owner instead, and let `check-contracts` hold the
  pointer true.
- No content that would surprise the user if they read it (skill-creator's principle of lack
  of surprise).

## How to test it

| What | How | Kind |
|---|---|---|
| Frontmatter keys are real | `check-contracts`' `frontmatter` claim | mechanical |
| It registers | `claude --plugin-dir <plugin> -p "List the skills you have from <plugin>"`; a typed skill will not be listed (above), so invoke it by name instead | load |
| It does the job | `run-evals` behavioral loop on `evals/sets/<skill>.json` | behavioral |
| Its description fires, and only in scope | `run-evals` trigger loop on `<skill>.trigger.json`; model-invoked skills only | trigger |
