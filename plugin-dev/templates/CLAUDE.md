# CLAUDE.md

Instructions for working on this repo — the `<name>` plugin source itself (its agents,
skills, and site), not a repo the plugin is used against.

## Shared protocol

Versioning, eval logging and the reading site are not defined here. They come from the
`plugin-dev` plugin, which is installed from the `cott-plugins` marketplace and applies to
every plugin repo:

- **`bump-version`** — when to bump patch/minor/major, and the bump + CHANGELOG + tag +
  marketplace procedure. Run it in the same commit as the change that triggered the bump.
- **`log-eval`** — every test run against this plugin's own skills or agents gets a dated
  file under `evals/` with the commit and model it was tested against, plus a row in
  `evals/README.md`. Every time, including a clean pass.
- **`build-site`** — rebuilds `site/docs/` and `site/mkdocs.yml` from the bundle. Re-run
  after editing any agent or skill.
- **`plan-phases`** / **`run-phase`** — a change too big for one chat is split into phases
  under `site/notes/`, one chat and one commit each, with a progress ledger between chats.

If `plugin-dev` is not installed, install it (`/plugin install plugin-dev@cott-plugins`)
rather than reinventing the protocol here.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions — currently its per-agent
`model:` choices. Anything true of every plugin belongs in `plugin-dev`, not here.

<!-- Add anything specific to this plugin's source below. -->
