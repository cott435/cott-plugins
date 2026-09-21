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

A skill is exactly an instruction that travels. So the policy is a set of skills, the builder
rides along in the same bundle, and every plugin repo keeps a `CLAUDE.md` that is a pointer
rather than a copy. Installing this plugin is what makes the protocol apply.

## The skills

Eight skills, in three groups by how they start. The table is the one list of them: a
`contracts.yml` claim fails when a directory under `skills/` has no row here.

| Skill | Starts | What it does |
|---|---|---|
| `log-eval` | on its own, every test run | Records a test against a plugin's own skills or agents as a dated file under `evals/` with the commit and model it ran against, plus an index row. A clean pass exactly like a failure. |
| `build-site` | on its own, after any agent or skill edit | Rebuilds `site/docs/` and `site/mkdocs.yml` from the bundle. |
| `check-contracts` | on its own, beside `build-site` and before any bump | Runs the cross-file claims in a bundle's `contracts.yml`: a heading one file parses and another owns, a pattern no file may contain, a list of names that goes stale. A `FAIL` names the `file:line`. |
| `run-evals` | on its own, whenever a phase or change calls for evals | Runs one skill's or agent's evals from its committed set in `evals/sets/`: mechanical checks, a load check, behavioral runs against a baseline graded assertion by assertion with skill-creator's grader, benchmark and viewer. Stops for your review, then records the result with `log-eval`. |
| `new-plugin` | on its own, when a plugin is started | Scaffolds a plugin subdirectory from `templates/` and adds its row to the marketplace. |
| `plan-phases` | when you type it | Expands a change too big for one chat — or a new plugin — from an idea into an approved design: interviews you in rounds, composes your jobs into shared layers (per-unit readers fanned out in parallel, a status per entity, a peer comparison, thin commands on top), publishes the proposal as a page with the flow chart rendered (its own suggestions marked) and waits for your yes. Then splits it into phases: a branch, an overview note, one note per phase, a progress ledger, all under `site/notes/`. Each phase is sized for one chat and carries its own evals. Commits the design set as phase 0. |
| `run-phase` | when you type it, once per chat | Does the next unfinished phase: reads the overview, the ledger and that one note; makes exactly its edits; runs the plugin's rules, `check-contracts`, `build-site` and the phase's evals; logs them; commits once; updates the ledger; stops. |
| `bump-version` | only on your yes | Decides patch/minor/major from what changed, bumps `plugin.json` and the marketplace row, writes the CHANGELOG line, tags, pushes. Proposes itself in chat and waits. |

## The rest of the bundle

| Path | What it is |
|---|---|
| `scripts/build_site.py` | The site builder. Fully generic — everything is discovered from the bundle. |
| `scripts/contract_sweep.py` | The contracts checker. Shared, so a change to it gets a positive and a negative run before it is committed (this plugin's `CLAUDE.md`). |
| `scripts/defaults/` | `mkdocs-base.yml` and `extra.css` used when a plugin doesn't override them. |
| `templates/` | The files a new plugin subdirectory starts with. |
| `templates/phases/` | The overview, phase-note and ledger shapes `plan-phases` writes. |
| `site/workflows/` | The three workflows below, one page each, rendered on the reading site. |

## Workflows

Three ways work reaches a plugin. Each is a page under `site/workflows/`; the summaries
here say which skills run, in what order, and which of them wait for you.

**[A new plugin](site/workflows/new-plugin.md).** From the repo root,
`/plugin-dev:plan-phases --new <name>`: it reads the closest existing plugin for
conventions, interviews you in rounds about what the plugin is for, composes the jobs into
shared layers, publishes the proposal as a page with a rendered flow chart of every agent and
command (its suggested additions marked), and waits for your yes. Only then does it invoke
`new-plugin` for the scaffold and marketplace row and write the design set — phase 1 is the
smallest bundle that loads, every later phase adds to it, and every phase's evals go into
`evals/sets/` in the same phase-0 commit. Then one chat per phase:
`/plugin-dev:run-phase 0.1` from `<name>/`, each running that phase's evals through
`run-evals` against those sets. The last phase proposes tagging `0.1.0`; `bump-version` does
it on your yes. A plugin that will only ever be one or two skills skips the phases:
`new-plugin`, write them, `build-site`, `check-contracts`, `run-evals` on whatever is
behavioral, propose the tag.

**[A small change](site/workflows/small-change.md).** One agent or skill, one chat. Edit;
the plugin's own rules (`CLAUDE.md`); `check-contracts`; `build-site`; if the edit changes
what an agent *does*, `run-evals` on the target's set in `evals/sets/` — the new case added
to the set first — logged with `log-eval` before results are reported; one commit. If it
looks bump-worthy, `bump-version` says so and waits.

**[A large change, in phases](site/workflows/phased-change.md).** Inside the plugin,
`/plugin-dev:plan-phases <slug>`: it researches what the change touches, interviews you in
rounds, publishes the proposal as a page with the changed flow chart rendered (new, changed
and suggested components marked) and waits for your yes; then it writes the branch, the
overview, one note per phase and the ledger, and commits phase 0 — with every behavioral
eval's prompts and expectations written into `evals/sets/`. Then one fresh chat per phase,
each opened with nothing but `/plugin-dev:run-phase <slug>`, which runs that phase's evals
through `run-evals` and stops for your review of the viewer before it commits, until the
ledger's last row is `done` and the last phase has proposed the bump.

What is the same in all three: every eval is a file before it is a sentence in chat; evals
run through `run-evals` from committed sets in `evals/sets/`; the site is rebuilt after
every agent or skill edit; contracts are checked before every commit that touches one; and
nothing is bumped, tagged or pushed without a yes.

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

Requires `pip install mkdocs mkdocs-material pymdown-extensions` once per
machine. The nav is
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
