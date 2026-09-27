# 11 — the bundle, the end-to-end eval, the release proposal

Phase 11. Deletes the eight removed workflow skills, brings `contracts.yml` to its final shape,
rewrites `README.md`, `VERSIONING.md`, the manifest description, `site/flow.md`, the five
`site/workflows/` pages and `site/site.yml`, writes `CHANGELOG.md`'s unreleased section with the
breaking-changes table, rebuilds the site, runs `check-contracts`, runs the end-to-end eval on
the two-package fixture with the fixed cost per spawn measured against eval L, and proposes the
release in chat. `bump-version` runs only on the user's yes. The gap it closes: nothing else
tells a user what the plugin now is.

## Decisions

- **Release level: minor** (`0.7.0`): breaking changes under `0.x` are a minor bump per
  `bump-version`'s policy. Proposed, never run here.
- **The end-to-end eval** is a behavioral row on `run-package` whose executor runs the real
  commands headless against a `reset.sh` copy of the fixture in the scratchpad (as eval K did),
  never inside the plugin repo: `/dev-team:plan-repo`, `/dev-team:plan-package data`,
  `/dev-team:run-package data`, `/dev-team:plan-package analysis`, `/dev-team:run-package
  analysis`, `/dev-team:finalize-project`, each `claude -p --plugin-dir <plugin> --output-format
  stream-json`. The stream files are copied into `outputs/` and are the measurement source.
- **Fixed cost per spawn** is read from each subagent's first assistant turn `usage` in the
  stream, per role, as eval L did; recorded in the log as a table beside L's numbers.
- **Manifest description**: `Plan, build, review and document Python monorepo packages
  section by section: one driver over derived state, six specialist agents, hooks for every
  mechanical check.`

## Files

| Path | Change |
|---|---|
| `skills/plan-change/`, `sync-design/`, `review-plan/`, `finalize-package/`, `review-package/`, `test-section/`, `implement-section/`, `review-section/` | deleted |
| `contracts.yml` | final: every remaining claim's `files:` and readers name only files that exist; the `plan-loop-exit` claim's old `files:` entries removed; the directory-name forbid's exemption list kept; a `names_listed`-style check for `agents/*` is the phase-2 hook claim (no new claim) |
| `.claude-plugin/plugin.json` | `description` only |
| `README.md` | rewritten in full — specification below |
| `VERSIONING.md` | "seven agents" → the eight files and six roles; the model table's rows for tester and designer updated (spawned by the driver) |
| `CHANGELOG.md` | `## [Unreleased]` section: the breaking-changes table from the overview, Added / Changed / Removed |
| `site/flow.md` | rewritten: where truth comes from (README over design, `interface.md` over contract, probe doc over assumption); the loop as the design's run-package chart; hand-offs; order of authority (five documents); the `docs/` map (the design's file table) |
| `site/workflows/new-repo.md`, `add-package.md`, `change-shipped-code.md`, `adopt-existing-repo.md`, `rebuild-from-legacy.md` | rewritten to the new commands |
| `site/site.yml` | `workflow_skills_order`: `shape-brief`, `set-constraints`, `extract-legacy`, `plan-repo`, `plan-package`, `run-package`, `probe-source`, `sync-plan`, `map-repo`, `finalize-project`, `status` |
| `evals/fixtures/two-package/README.md` | the "What each eval expects of it" table gains the remake's end-to-end row |

## Specification

### `README.md`

Sections, in order: title and two paragraphs (what it is; you drive it; a repo of packages);
`## Contents` (the overview's tree without the change markers, one line per file, the
`hooks/` entries included); `## One-time setup` (install; `/agents` lists eight; auto or
acceptEdits; `/model`; `/dev-team:status`; a git branch; hooks run in every session the
plugin is enabled in and exit 0 outside a dev-team repo); `## Which skill to run` (the new
table: rough idea → `shape-brief` then `plan-repo`; quality bar → `set-constraints`; new repo →
`plan-repo`, per package `plan-package` then `run-package`; existing repo → `map-repo` then
`run-package` lowest package first; a change to shipped code → `plan-package <pkg>` (or
`plan-repo`) then `run-package`; one step by hand → `run-package <pkg> <section> --step`; an
API changed → `probe-source`; rebuilding from legacy → `extract-legacy` twice then `plan-repo`;
human-facing docs → `finalize-project`; lost track → `status`); `## Running a package` (the
driver: run gate, derived state, the ready set, the loop per section, the caps and `--defer`,
the ask step, the close, the summary); `## The states` (the nine states in one table with the
rule for each, copied from `status.py`'s docstring — the one place besides the script; the
state-vocabulary claim gains README as a reader); `## Hooks` (the three, what each runs, the
marker and the counter, "exit 0 outside a dev-team repo"); `## Questions` (the interview rule
and the driver's ask step); `## Decisions` (the ledger, as today); `## Deviations and
spec-changes` (the ledger entry, who writes which status, how a spec-change re-opens a step);
`## Reviews` (two reviewers in round 1, diff-scoped rounds, the closed CRITICAL list, the cap,
defer); `## Code conventions` (the knowledge-skill table with the new routing: `git-workflow`
preloaded into every committing agent; `security-review` implementer and reviewer; TDD
implementer only, read by the tester; `reserved-skill-names` row gone); `## docs/ layout` (the
design's file table as a tree); `## Gotchas` (kept where still true: probes make real calls;
work on a branch; re-running continues; the driver is a loop in your conversation; return size;
descriptions are always loaded; nesting depth; adopted repos block on decisions;
`lint-imports` needs importable packages; strict docs build; parallel implementers as a
non-goal; `claude --agent implementer`). Gone: instruction-only boundaries (the guard hook
exists), finalize-package's partial mode, spine-first.

Every command in the file is `/dev-team:`-prefixed; the `no unprefixed plugin command` claim
covers the file.

### `site/workflows/*.md`

- `new-repo.md`: `shape-brief` → `set-constraints` (optional) → `plan-repo` → per package
  `plan-package <pkg>` → `run-package <pkg>` (the whole loop, the surface, the close) →
  `plan-package <next>` … → `finalize-project`.
- `add-package.md`: `plan-repo "<addition>"` (Extend; the change list; a bound dependency →
  a change file) → `plan-package <new>` → `run-package <new>`; a change file on a shipped
  package → `run-package <that pkg>` re-opens its sections at DESIGN → `sync-plan` closes.
- `change-shipped-code.md`: `plan-package <pkg> "<change>"` (CHANGE → `docs/changes/<slug>.md`)
  → `run-package <pkg>` (the named sections re-open at DESIGN in `delta` mode; consumers in
  **Downstream impact** likewise) → the close applies the change file.
- `adopt-existing-repo.md`: `map-repo` (three phases; the monolith stop) → `run-package <pkg>`
  lowest first (`document` designs, green intent suites, READMEs, reviews) → `finalize-project`.
- `rebuild-from-legacy.md`: `shape-brief` → `extract-legacy` twice → `plan-repo` → the new-repo
  loop; a colliding skill name reported by the architect.

## Steps

1. Delete the eight skills; `site/site.yml`; the README tree (the two-file rule).
2. `contracts.yml` final; `check-contracts` — every claim PASS, and every `files:` glob matches.
3. `README.md`, `VERSIONING.md`, `plugin.json` description, `site/flow.md`, the five workflow
   pages, `CHANGELOG.md` unreleased, the fixture README row.
4. `build-site`; open `site/docs/index.md` and the nav: no page for a removed skill.
5. Evals, through `run-evals`, logged with `log-eval`; the fixed-cost table in the log.
6. Commit: `dev-team remake (phase 11): removed skills deleted; README, site, changelog; end-to-end eval`.
7. In chat: propose `bump-version` at **minor** (`0.7.0`) with the CHANGELOG's unreleased
   section as the entry, and stop. Nothing bumps, tags or pushes here.

## Evals

| ID | Kind | Target | Baseline | Set evals | Pass bar |
|---|---|---|---|---|---|
| 11.1 | mechanical | `contracts.yml` | — | `check-contracts` | all PASS; `python3 -c` listing every `files:` and `owner:` path confirms each exists |
| 11.2 | mechanical | `README.md`, `site/site.yml` | — | the two `names_listed` claims | PASS after the deletions; planting a stray `test-section` line in `site.yml` FAILs |
| 11.3 | load | the bundle | — | `claude --plugin-dir ./dev-team -p "List the skills and agents you have from dev-team"`; then `/agents` interactively | eight agents; the knowledge skills listed; no removed skill named |
| 11.4 | behavioral | `run-package` | previous | `evals/sets/run-package.json` 4 (end-to-end) | every expectation passes for `with_skill`: both packages `shipped: yes` in `status.py`; 398 rows stored and a second run stores nothing; every section has a round with `approve`; one commit per agent run, each with a `Dev-Team-Run:` trailer; `docs/followups.md` holds no `— review` line; the fixed cost per role is recorded and the tester's and reviewer's are below eval L's (40k, 38k); the summary's `next:` after `analysis` is `/dev-team:finalize-project` |

## Done when

- `ls skills/` lists exactly: `debugging-and-error-recovery`, `extract-legacy`, `finalize-project`, `git-workflow-and-versioning`, `map-repo`, `plan-package`, `plan-repo`, `planning-templates`, `probe-source`, `project-structure`, `python-implementation`, `python-style-guide`, `run-package`, `security-review`, `set-constraints`, `shape-brief`, `status`, `sync-plan`, `test-driven-development`, `workspace-scaffold`.
- `check-contracts` all PASS; `build-site` exits 0; `grep -rc 'finalize-package\|review-plan\|sync-design\|plan-change\|map-project\|implement-section\|test-section\|review-section\|review-package' README.md site/flow.md site/workflows/ agents/ skills/` is 0 everywhere except `CHANGELOG.md` and `site/notes/`.
- `CHANGELOG.md` has an `## [Unreleased]` section with the eight breaking changes.
- Logs for 11.1–11.4 in `evals/README.md`; the fixed-cost table is in 11.4's log.
- The ledger row for phase 11 reads `done`, and the chat ends with the bump proposal.
