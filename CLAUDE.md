# CLAUDE.md

This repo (`cott-plugins`) is a marketplace bundled with every plugin it lists, each as its
own subdirectory. This file is the shared protocol every plugin here follows. A plugin's own
`CLAUDE.md`, in its subdirectory, holds only what's specific to that plugin — its own
`VERSIONING.md` pointer, its own gotchas — and points back here for everything else.

## Adding or changing a plugin

Six skills, all from the `plugin-dev` plugin (installed alongside everything else here —
`/plugin install plugin-dev@cott-plugins` if it's ever missing). None of these are commands
you type — each is a normal skill — but they don't all run the same way:

**Run automatically, no need to ask** — Claude invokes these on its own when the moment
matches, because none of them commit or push anything on their own:

- **`new-plugin`** — scaffolds a new plugin as a subdirectory here and adds its row to
  `.claude-plugin/marketplace.json`. There's no other way a new plugin gets set up correctly
  (its own `.claude-plugin/plugin.json`, `CLAUDE.md`, `VERSIONING.md`, `evals/`,
  `site/site.yml`).
- **`log-eval`** — every test run against a plugin's own skills or agents gets a dated file
  under that plugin's `evals/`, with the commit and model it was tested against, plus a row
  in `evals/README.md`. Every time, including a clean pass, and written *before* reporting
  results back — a test that exists only in a conversation is a test nobody can check later.
- **`build-site`** — rebuilds `<plugin>/site/docs/` and `<plugin>/site/mkdocs.yml`. Re-run
  after editing any agent or skill in a plugin that has a `site/`. Always check the workflows affected by the adits and update them accordingly.
- **`check-contracts`** — runs the cross-file claims a plugin declares in its own
  `contracts.yml`: a heading one prompt parses against the template another owns, a rule one
  file states and another contradicts, a list of names that goes stale when a directory
  changes. Re-run beside `build-site` after editing any agent or skill, and always before
  proposing a bump. A `FAIL` names the exact `file:line`; fix the file rather than relaxing
  the claim.

**Run when you type them** — two skills for a change too big for one chat. Neither
pushes; both commit, which is why the model never starts them on its own:

- **`plan-phases`** — splits a change into phases, each sized for one Claude Code chat:
  a branch, `site/notes/<slug>-00-overview.md`, one note per phase, and a progress ledger.
  Commits the design set as phase 0. With `--new <name>` from the repo root it starts a
  plugin the same way — `new-plugin`'s scaffold is its phase 0 — so a plugin with agents or
  more than a couple of skills is never written in one sitting.
- **`run-phase`** — the next unfinished phase, in a fresh chat: exactly that note's edits,
  the checks above, its evals logged, one commit, the ledger updated, then stop. Every chat
  of the change starts with `/plugin-dev:run-phase <slug>` and nothing else.

**Asks first, always** — `bump-version` decides patch/minor/major, bumps a plugin's
`.claude-plugin/plugin.json` and its row in the root `marketplace.json`, writes a
`CHANGELOG.md` line, tags the commit, and pushes. That's several things worth a yes before
they happen, so it never runs on its own: when a change looks bump-worthy, Claude says so in
chat and names the level it would pick, then waits. Only a reply along the lines of "yes" or
"go ahead" makes it actually edit anything, commit, tag, or push.

The first four are still a judgment call, not a guarantee — if the automatic three don't fire when
you expect, or `bump-version` doesn't speak up when you think it should, ask for it directly.

## Working in one plugin

Other plugins' uncommitted files are not this chat's business unless asked about
directly — don't flag them, and never stage them incidentally. Stage and commit by
plugin path (`git add dev-team/`), never `git add -A` or a bare `git add .` at the
repo root.

Commits and pushes in this repo happen in Claude Code, not Cowork — a Cowork-run
`git commit` can get killed mid-write by its own tool timeout and leave a stale
`.git/index.lock` behind. Cowork is fine for reading, discussing, and drafting; the
commit-bearing steps (`plan-phases`, `run-phase`, `bump-version`) run in Claude Code.

## Layout

```
cott-plugins/
├── .claude-plugin/marketplace.json   every plugin below, by relative path — kept in step
│                                      with each plugin's own version by bump-version
├── plugin-dev/                       this protocol, packaged as a plugin like any other
├── dev-team/                  a plugin
└── <next plugin>/                    a plugin
```

See the root `README.md` for why this is one repo instead of several, and what
`marketplace.json` is for versus `plugin.json`.
