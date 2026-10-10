# CLAUDE.md

Instructions for working on this subdirectory — `plugin-dev`'s own source (its skills,
scripts, templates) — not the general protocol, which is the repo root `CLAUDE.md` and
applies here the same as everywhere else in `cott-plugins`.

## Repo-specific

`VERSIONING.md` holds this plugin's own versioning decisions, including the one agent's
`model:` choice.

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
  `check-contracts` fails otherwise. `site/workflows/` holds the five workflow pages the
  README summarizes; a change to how work reaches a plugin is a change to both.
- **`scripts/build_site.py` is shared.** A change to it changes every plugin's site at once.
  Before committing one, rebuild at least `dev-team` and diff the output — its site is
  the reference the builder was verified against.
- **`run-evals` is shared.** Its `references/eval-kinds.md` is the one list of eval kinds;
  `plan-phases` and its eval writers write the overview's eval rows and the sets against it,
  and `run-phase` runs them through it. A kind added or renamed there is a change to all three, and
  `check-contracts`' eval-kinds claim fails until they agree. Eval sets under `evals/sets/`
  are committed; `evals/workspace/` never is. Its `references/prompts.md` is the one copy of
  the executor and grader prompts, read by `eval_workspace.py run` by heading; a change to
  the script's `init`, `run` or `report` is checked with
  `python3 evals/fixtures/run-evals-runner/check.py`, which needs no model.
- **`scripts/phases.py` owns the ledger and reads the overview.** It parses the ledger's
  table by its column names, the overview's `## Phases` and `## Evals by phase` tables, and
  the `**Checkpoints:**`, `**Init flags:**` and `**Checks:**` lines, all as
  `templates/phases/` writes them. A column renamed in a
  template is a change to the script, and `python3 evals/fixtures/phases/check.py` (no
  model) is run before either is committed.
- **This plugin has hooks, and they run in every session on every machine.** Each exits 0
  before doing anything unless its event names a run-evals iteration or the plugin directory
  has a phase in flight, and each exits 0 with the reason on stderr when it crashes. Keep
  both properties in any hook added here; `evals/fixtures/phases/check.py` pipes the events.
- **`templates/phases/design.md` is the one list of the design's sections**, as its `##`
  headings. `design-plugin` writes from it and `plan-phases` reads the design by those names.
  Renaming a section is a change to both, and `check-contracts` fails until they agree.
- **`templates/review/edits.md` is the one list of the edit list's sections**, the same way
  for `review-plugin`'s spec: `review-plugin` writes from it, `plan-phases` and `run-phase`
  read it by those names, and `check-contracts` fails until they agree. Its item fields and
  the findings file's fields (`templates/review/findings.md`) are parsed by
  `scripts/edits.py`; a field renamed in a template is a change to the script, and the
  script is run against the real `dev-team/site/notes/determinism/` review before it is
  committed.
- **`plugin-anatomy` is the source of truth for platform facts.** A fact about how a plugin
  component behaves is stated there once, with its source and its status (`[docs]`,
  `[proven: …]`, `[unconfirmed]`), and cited from everywhere else. When the docs or an eval
  change a fact, fix it there. Its `frontmatter-keys` blocks are read by `contract_sweep.py`'s
  `frontmatter` check, so a key added to or removed from them changes what every plugin's
  sweep accepts.
- **`scripts/contract_sweep.py` is shared too**, and a checker that cannot fail is worse than
  none. A change to it gets both runs before it is committed: the real bundle, which must
  still pass, and a copy with a deliberate defect per check kind, which must still fail —
  `evals/2026-09-17-contract-sweep-negative.md` is the worked example.
