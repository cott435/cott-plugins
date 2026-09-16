# cott-plugins

One repo: a marketplace and every plugin it lists, bundled together as subdirectories. Clone
it once and everything is here — the catalog and the content both.

```
cott-plugins/
├── .claude-plugin/
│   └── marketplace.json    the catalog: which plugins exist, where each one lives in this repo
├── plugin-dev/              a plugin — shared versioning, eval logging, the site builder
└── project-workers/         a plugin — plan/build/review Python monorepo packages
```

## Use it

```
/plugin marketplace add cott435/cott-plugins   # once per machine
/plugin install plugin-dev@cott-plugins        # every machine
/plugin install project-workers@cott-plugins   # only the machines that use it
```

`marketplace add` clones this whole repo — after that, `install` just points Claude Code at
one subdirectory of the copy it already has. So you still choose per plugin, per machine; the
only thing bundling changes is that every machine ends up with a local copy of every plugin's
*source*, not just the ones it has installed. For a repo of markdown and small scripts, that
costs nothing.

To pick up a change after a git pull: `/plugin marketplace update cott-plugins`.

## `marketplace.json` vs `plugin.json`

Both live under `.claude-plugin/`, which is the only reason they get confused. They are
different kinds of file doing different jobs.

| | `plugin.json` | `marketplace.json` |
|---|---|---|
| Lives in | each plugin's own subdirectory | the repo root, once |
| Answers | "what *is* this thing?" | "what exists, and where in this repo is it?" |
| Contains | name, version, description, author | a list of plugins, each with a `source` |
| Read when | the plugin is loaded | you run `/plugin marketplace add` or `install` |
| Makes | agents, skills and commands available | names installable |

A **plugin** is content Claude actually runs. `project-workers/.claude-plugin/plugin.json`
is that plugin's identity card: the `name` there becomes the namespace for everything in the
bundle, which is why its skills are invoked as `/project-workers:plan-repo`.

A **marketplace** is a catalog — it runs nothing itself. Each entry names a plugin and a
`source`. In a bundled repo like this one, `source` is just a relative path to that plugin's
subdirectory:

```json
{ "name": "plugin-dev", "source": "./plugin-dev", "version": "0.1.0" }
```

(A marketplace can instead point `source` at a completely separate repo on GitHub — that's
the multi-repo layout this one used to be. Both are valid; this one is bundled because it's
simpler to work with day to day.)

The `version` in an entry should match that plugin's own `plugin.json` — keeping the two in
step is what `bump-version` (in the `plugin-dev` plugin) is for.

## `plugin-dev` isn't special to this repo

It's a plugin like `project-workers` — its own `plugin.json`, its own skills, listed here
like anything else. The only unusual thing about it is what its skills are *about*: the
shared rules (versioning, eval logging, the site builder) that every plugin in this repo
follows. That's why it's worth installing everywhere, even though to `marketplace.json` it's
just another row.

## Adding a plugin

```
mkdir -p <name>/.claude-plugin
# write <name>/.claude-plugin/plugin.json, agents/, skills/, etc. — see plugin-dev's
# new-plugin skill for the full scaffold
```

Then add a row to `marketplace.json`:

```json
{ "name": "<name>", "source": "./<name>", "description": "<one line>", "version": "0.1.0" }
```

Commit, push, and `/plugin marketplace update cott-plugins` on each machine.
