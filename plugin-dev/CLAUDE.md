# CLAUDE.md

Instructions for working on this subdirectory — `plugin-dev`'s own source (its skills,
scripts, templates) — not the general protocol, which is the repo root `CLAUDE.md` and
applies here the same as everywhere else in `cott-plugins`.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions. It has no agents, so there's
no `model:` field to set — see that file for why.

## This plugin in particular

It defines the protocol every other plugin in this repo follows, so a few things need extra
care when editing it:

- **Skill descriptions.** These skills are installed on every machine and are live in every
  session, including sessions that have nothing to do with plugins. Each description says
  "only inside a plugin's own subdirectory (one containing `.claude-plugin/plugin.json`)"
  for that reason. If you widen a description, check it doesn't start firing in unrelated
  repos.
- **This bundle has its own `contracts.yml`.** The README's **The skills** table is the one
  list of skills and `site/site.yml` the run order of the typed ones; adding a skill means a
  row in the first and, if it is typed, a line in the second, in the same commit.
  `check-contracts` fails otherwise. `site/workflows/` holds the three workflow pages the
  README summarizes; a change to how work reaches a plugin is a change to both.
- **`scripts/build_site.py` is shared.** A change to it changes every plugin's site at once.
  Before committing one, rebuild at least `dev-team` and diff the output — its site is
  the reference the builder was verified against.
- **`run-evals` is shared.** Its `references/eval-kinds.md` is the one list of eval kinds;
  `plan-phases` and its eval writers write notes and sets against it, and `run-phase` runs
  them through it. A kind added or renamed there is a change to all three, and
  `check-contracts`' eval-kinds claim fails until they agree. Eval sets under `evals/sets/`
  are committed; `evals/workspace/` never is.
- **`design-plugin` owns the design's section list** ("3. The writeup" in its `SKILL.md`), and
  `plan-phases` reads the design by those names. Renaming a section is a change to both, and
  `check-contracts` fails until they agree. `templates/phases/design.md` mirrors the list; keep
  its headings in the same order.
- **`scripts/contract_sweep.py` is shared too**, and a checker that cannot fail is worse than
  none. A change to it gets both runs before it is committed: the real bundle, which must
  still pass, and a copy with a deliberate defect per check kind, which must still fail —
  `evals/2026-09-17-contract-sweep-negative.md` is the worked example.
