# plugin-dev

The shared kit every other plugin is built with: how a plugin is versioned, how a test run
against it is recorded, and how its reading site is generated. One copy, installed as a
plugin, instead of the same three conventions drifting apart across repos.

## Why this is a plugin and not a folder

The things being shared are two different kinds of thing, and only one of them is code.

The site builder is code, so it lives in `scripts/` and is invoked with a path. But the
versioning policy and the eval convention are *instructions for Claude* — the reason the eval
protocol works at all is that something tells Claude to write the file every time. A shared
folder can't do that; a `CLAUDE.md` copied into every repo can, but then there are N copies
to keep in sync, which is the problem being solved.

A skill is exactly an instruction that travels. So the policy is three skills, the builder
rides along in the same bundle, and every plugin repo keeps a `CLAUDE.md` that is a pointer
rather than a copy. Installing this plugin is what makes the protocol apply.

## What's here

| Path | What it is |
|---|---|
| `skills/bump-version/` | Semver policy and the bump + CHANGELOG + tag + marketplace procedure, plus the `model:` field policy. Proposes itself in chat and waits for a yes — the one skill here that never runs unasked. |
| `skills/log-eval/` | The eval record convention: one dated file per test run, with the commit and model it was tested against. |
| `skills/build-site/` | Builds the MkDocs reading site for whatever plugin repo you're in. |
| `skills/new-plugin/` | Scaffolds a new plugin repo from `templates/` and registers it in the marketplace. |
| `skills/check-contracts/` | Checks the cross-file claims a bundle's own prompts act on — a heading one file parses and another owns, a rule one file states and another contradicts, a list of names that goes stale. Reads each bundle's `contracts.yml`. |
| `scripts/build_site.py` | The builder itself. Fully generic — everything is discovered from the bundle. |
| `scripts/defaults/` | `mkdocs-base.yml` and `extra.css` used when a repo doesn't override them. |
| `templates/` | The files a new plugin subdirectory starts with. |

## Install

```
/plugin marketplace add cott435/cott-plugins
/plugin install plugin-dev@cott-plugins
```

Install this one on every machine — the point is that its skills apply to whatever else
lives in this repo.

## The repo layout, and why

This plugin lives inside `cott-plugins`, one directory among several:

```
cott-plugins/
├── .claude-plugin/marketplace.json   the catalog — every plugin below, by relative path
├── plugin-dev/                       this kit
├── dev-team/                  a plugin
└── <next plugin>/                    a plugin
```

One repo, one clone, one push/pull. `marketplace.json` still lets you `/plugin install` each
plugin independently on whatever machine wants it — bundling only means the *source* of every
plugin is on disk everywhere the repo is cloned, not that every plugin is *installed*
everywhere. For a repo of markdown and small scripts, carrying the source of a plugin you
haven't installed costs nothing.

The trade-off, honestly: a single repo can't version or tag one plugin without touching the
tag namespace of the others, and a change to `dev-team` shows up in `plugin-dev`'s git
log even though nothing in `plugin-dev` changed. `bump-version` still works — see below — it
just tags the whole repo rather than one plugin's own history. If a plugin ever needs to be
shared outside this account, or versioned on a schedule independent of everything else here,
that's the point to split it back out into its own repo and point `marketplace.json` at
`{"source": "github", "repo": "...", "ref": "..."}` instead of a relative path — both are
valid `source` shapes, and moving between them later doesn't require rewriting anything else.

## A new machine

```
git clone git@github.com:cott435/cott-plugins.git ~/dev/cott-plugins
```

One clone gets the catalog and every plugin's source. Then add the marketplace and install
what that machine actually needs — the marketplace file is already on disk, so `marketplace
add` just points Claude Code at the local clone:

```
/plugin marketplace add ~/dev/cott-plugins
/plugin install plugin-dev@cott-plugins
```

(Or `/plugin marketplace add cott435/cott-plugins` to have Claude Code manage its own clone
instead of using yours — either works; using your own clone means one copy on disk instead of
two.)

## Working on a plugin with two machines

Ordinary git: push from one, pull on the other, same as any repo. A release still needs a
version bump and a tag — `bump-version` below — the only difference from a multi-repo layout
is that the tag names the whole repo's state, not one plugin in isolation, so tag messages
should say which plugin the release is actually about.

## The reading site

```
python3 ~/dev/cott-plugins/plugin-dev/scripts/build_site.py   # from any plugin subdirectory
cd site && mkdocs serve
```

Requires `pip install mkdocs mkdocs-material pymdown-extensions` once per machine. The nav is
generated from what the script finds, so a new agent, skill, command, rule or `references/`
file appears without editing any config:

    Home (README) -> The flow -> Workflows -> Agents -> Commands ->
    Workflow skills -> Knowledge skills -> Rules and config -> Notes -> Evals

A section with nothing in it is omitted. A skill is a **workflow skill** when its frontmatter
says `context: fork` and a **knowledge skill** otherwise. `site/docs/` and `site/mkdocs.yml`
are generated and gitignored in every plugin repo; `site/site.yml`, `site/flow.md`,
`site/workflows/` and `site/notes/` are authored and committed. Every key in `site.yml` is
optional — a plugin with no site config at all still builds.

See `skills/build-site/SKILL.md` for the full contract.
