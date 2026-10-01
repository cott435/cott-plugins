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

## Deviations

- **"Done when"'s grep reached files the Files table does not list.** Step 1 and the Files
  table name the eight deleted skills and the bundle's docs. But the grep for removed command
  names must be 0 across `agents/` and `skills/`. Five kept skills still named them:
  `shape-brief` (`SKILL.md`, `references/brief.md`), `project-structure`,
  `set-constraints/references/constraints-template.md` and `python-style-guide`. What was done:
  each mention was re-pointed to what replaced it (`map-repo`; a change file through
  `plan-package`; the `surface` section; `run-package data ingest`; the stop gate). Three
  mentions of the deleted `surface.md` remain, in `test-driven-development`, `repo-contract.md`
  and `python-style-guide`. The grep does not cover `surface.md`, so they are *noticed*.
- **`contracts.yml`: README joins the state-vocabulary claim by span**, not `cites`. The
  README's **The states** table is bolded state names, and the span checks each against
  `status.py`'s rule list.
- **11.3's `/agents` step was not run.** It is interactive. The headless listing (`claude -p
  --plugin-dir`, the installed dev-team disabled) showed the eight agents and nine knowledge
  skills. Workflow skills are `disable-model-invocation: true`, so the model does not list
  them. The e2e streams load `plan-repo`, `plan-package`, `run-package` and
  `finalize-project` from the working tree.
- **11.4 was run by a script runner, not an executor subagent**, as in phase 8. In this
  session `dev-team:<agent>` resolves to the installed 0.6. `step.sh`, `chain*.sh`, `tail*.sh`,
  `post.py` and `commits.py` lived in the session scratchpad and are not committed. Both
  plugin copies left out `evals/`, per the ledger. The baseline copy kept `site/notes/`, and its
  5-run driver read `remake-08-run-package.md` while diagnosing its own stop. That changed
  nothing, since it stopped regardless.
- **11.4 needed three fixes outside the Files table, each on the user's call.**
  1. *Iteration 4* stopped in `run-package data` at `data/clean DESIGN`. An implementer's
     `spec-change:design` entry is never closed: the designer and tester never set a
     spec-change's `Status:`, and only the architect resolves `spec-change:contract`. So
     `status.py` re-opened DESIGN on every call. Fix: `status.py` derives it. An open
     `spec-change:design` counts only until the design is committed after the commit that added
     the entry, and a `spec-change:test` only until the intent tree is. The table's spec-change
     column and `--repo` follow the same rule. It comes with three state cases
     (`design-spec-change-answered`, `test-spec-change-test`, `test-spec-change-answered`) and
     the README's states table.
  2. *Iteration 5*, `run-package analysis`: Claude Code 2.1.270's Write tool refuses a
     subagent's write of any file matching `/^(REPORT|SUMMARY|FINDINGS|ANALYSIS).*\.md$/i`
     ("Subagents should return findings as text, not write report files"). So the designer
     could never write `design/report.md`. Fix: a naming rule in `project-structure` §4 and the
     package-contract template (no section or source name starts with those words; use one word
     that is also a Python package name), plus a README gotcha. The rename was then typed as a
     user change request in the same copy (4b). The request's name, `md-report`, was wrong:
     it is no Python package name, so the implementer built `md_report/`. A second request (4c)
     became a CHANGE file. A change to a built section's *path* cannot close: `status.py` reads
     the README at the contract's stale path, and `sync-plan` applies the change only at DONE.
     The driver asked for a human call, and the user hand-edited the path cell (`b71ff5e`).
  3. After the delta design, the tester correctly found no test to change and committed
     nothing, so "design newer than tests" kept the section at TEST. Fix: `tester.md`. A run on
     an existing tree that changes nothing still commits a one-line `conftest.py` stamp,
     summary `intent tests current with design`. `status.py` skips that summary where it
     re-opens IMPLEMENT or REVIEW, as it skips a regeneration. The message table in
     `git-workflow-and-versioning` lists it, and it comes with one state case
     (`test-design-newer-tests-current`).
- **Eval-set expectation 1 was corrected** to accept the report section under the name the
  contract gives it, per the platform fact above. The eval's `report` name can no longer be
  written.
- **The baseline was run once, in iteration 4, and carried into iteration 5.** Its driver is
  the 0.6 file. It stops at the missing DESIGN step (`data`) and the missing `integration.md`
  (`analysis`), and none of the three fixes touch that.
- **The fixed-cost bar compares across platform versions.** Eval L measured the reviewer at
  38,467 on the Claude Code of 2026-09-19. The same 0.6 reviewer holds 43,094 on 2.1.270. A
  same-version control, both plugins spawned with one trivial prompt, is in the log and in
  `fixed-cost.md`. Tester +0.4k, reviewer +0.3k, implementer +0.4k, designer +8.6k,
  architect +5.0k. The design's expected drop for the tester and reviewer did not happen.
- **11.4 missed its bar.** The bar: every expectation passes for `with_skill`. The result:
  5/9 against the 0.6 baseline's 2/9, after the three fixes above (a first iteration, then a
  from-scratch rerun and two resumed walks). Both packages shipped, 398 rows idempotent, and
  every section approved with a round-1 pair. The misses:
  - the tester's missing trailer and second commit (phase 8's *noticed* line);
  - the fixed-cost bar, set on eval L's platform (same-version tester and reviewer flat,
    designer and architect up);
  - prose around the summary block on stopped runs;
  - the driver's read-only diagnostic Bash calls.
  Log: `evals/2026-09-28-remake-phase11-bundle.md`.
- **Release level: major (`1.0.0`), not the note's minor (`0.7.0`).** The note said breaking
  changes under `0.x` are a minor bump per `bump-version`'s policy. That policy has no `0.x`
  exception: a removed or renamed command and a changed document format are major by its test.
  The user chose `1.0.0`.
