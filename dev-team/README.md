# dev-team

A Claude Code plugin that plans, builds, reviews and documents a Python monorepo, one section
of one package at a time. It plans a **repo of packages** (`data` → `analysis` → `ml`, say),
where each package's `surface` section, built last, publishes an `interface.md` that the next
package is planned and built against. A single-package repo is the same thing with one row
in the Packages table.

You drive it. Every workflow skill is one you type, so Claude never starts one on its own.

## How it runs

One driver, `/dev-team:run-package <pkg>`, runs in your conversation and takes every section
of a package to DONE. It is built the way every workflow in this repo is built, a thin
driver over agents, scripts, hooks and state on disk:

| Part | Here |
|---|---|
| **Driver** | `run-package`. Each turn it asks `status.py` for the ready set, spawns every ready section's next agent in one message, and branches on the first line of each return. It reads no design, no code and no report, and the one file it writes is your answer in `docs/decisions.md` |
| **Agents** | Nine, each answering one question. The architect writes the contracts, the researcher probes an external source, the profiler profiles the real data a data-heavy section receives, the designer designs a section, the tester turns the design into failing intent tests, the implementer builds it, the reviewer judges it, the documenter writes the human-facing docs, the curator surveys an old repo. Each is spawned with a block of `Field: value` lines that are its own **Inputs**, ends in one commit, and returns `Result: done \| blocked \| stopped \| spec-change \| design-gap` |
| **Scripts** | `status.py` derives every section's state from the documents, the code, git and the gate records on every call. `locked.py` serializes the three edits parallel implementers share |
| **Hooks** | A stop gate that will not let an implementer finish while its section's checks are red, write and shell guards that hold each agent to its own paths, a formatter on every edit, and a sync that folds each section's decisions into the one ledger |
| **Ledger** | None is kept. The state is derived, so a re-run after a crash, a hand edit or a week away picks up exactly where the files say |
| **Knowledge skills** | Scoped by role: preloaded through each agent's `skills:` frontmatter, or invoked when its procedure reaches them. Your own domain conventions go in project skills under `.claude/skills/`; the architect assigns each to a section, and the designer and implementer invoke them |

Why it is built this way:

- **Every mechanical check is a hook, not a reviewer's job.** No lint error, failing test or
  lowered bar reaches a reviewer, and a reviewer runs no command: the gate's record is its
  evidence.
- **A section is built from its own design and from what its dependencies shipped.** A
  dependency is read as its README, an upstream package as its `interface.md`, an external
  source as its probe doc. The document written from the thing beats the one written about
  it before it existed.
- **Sections run in parallel.** The ready set is every section whose dependencies are DONE,
  and each agent is confined to its own section's files, so designers, testers, implementers
  and reviewers for different sections run side by side.
- **Nothing lives in the conversation.** Subagents start fresh and cannot ask you anything,
  so a decision is an entry in `docs/decisions.md`, a disagreement between a document and the
  code is an entry in the section's deviations ledger, and a review is a report on disk.
- **Canonical contracts describe code that exists.** An edit that touches a built or shipped
  package becomes a change file, applied to the contracts once its sections are DONE and
  checked against the code.

## Where you are asked

The driver stops for you, once per block, and records your answer:

- a decision with no assumption, or a missing credential;
- a `repair` or `drop` treatment the profiler proposes, since it changes or removes data;
- a review loop at its cap (three rounds, two when a prior finding is unfixed): *one more
  round* or *defer*;
- an implementer that blocked, or was let through after three red attempts;
- a package whose surface check, integration check or paths review still fails.

Re-running the same command is the continue action after any stop, and
`/dev-team:status` prints where everything stands and the exact next command.

## Install and one-time setup

```
/plugin marketplace add cott435/cott-plugins
/plugin install dev-team@cott-plugins
```

In Cowork: Customize -> Plugins -> Add marketplace, then Install.

1. **Verify with `/agents`** before the first run: the nine agents must be listed. If they
   are not, run `/reload-plugins` or restart Claude Code. User-level definitions in
   `~/.claude/agents/` override same-named plugin agents, so those must not exist.
2. Run in **auto** or **acceptEdits** mode, not plan mode: subagents inherit your mode, and
   plan mode is read-only.
3. Every agent inherits your session model, so set `/model` before you start a run.
4. The repo you build in is a git repository on a feature branch. Every run starts with the
   run gate: not `main` or `master`, and a clean tree except `docs/decisions.md`,
   `docs/brief.md`, `docs/constraints.md` and `.claude/agent-memory/`, which you edit by
   hand between runs.
5. The five hooks run in every session the plugin is enabled in and exit 0 outside a
   dev-team repo, one with a `docs/architecture.md`. They check only the plugin's agents,
   never your own editing.
6. Merge `pyproject-lint-config.toml`, which ships beside this README, into the root
   `pyproject.toml` of a repo that predates the scaffold step. It needs ruff 0.16.0 or later.

## The reading site

Every agent, skill and script as a browsable site:

```
python3 ~/dev/cott-plugins/plugin-dev/scripts/build_site.py --build   # from this directory
python3 -m http.server --directory site/_build 8000                   # http://127.0.0.1:8000
```

Needs `pip install sphinx myst-parser furo sphinxcontrib-mermaid pyyaml` once per machine.
Or ask Claude: the `build-site` skill from `plugin-dev` does the same thing.

| On the site | Holds |
|---|---|
| **The flow** | Which command to type for what you have, which agent uses which skill, who writes and reads each document, the driver's loop, which document wins a disagreement |
| **Workflows** | One page per route: a new repo, adding a package, rebuilding from a legacy repo, changing shipped code, adopting an existing repo, pairing on a section |
| **Reference** | Running a package step by step and the states a section moves through; questions, decisions, deviations and reviews; what each hook checks; code conventions; the `docs/` layout; gotchas and upgrade notes |
| **Agents**, **Skills**, **Scripts** | Each file as written, found without any config |

`site/site.yml`, `site/flow.md`, `site/workflows/`, `site/reference/` and `site/notes/` are
authored and committed; `site/docs/` and `site/_build/` are generated and gitignored.

## Working on it

Read `CLAUDE.md` first. Versioning, eval logging, the contracts check and the site builder
are shared with every other plugin and live in the **`plugin-dev`** plugin, not here. To
check what a run's agents actually did, type plugin-dev's `audit-run` skill in a fresh chat
opened on this folder.
