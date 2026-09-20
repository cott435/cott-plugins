# Changelog

One entry per tagged release. The versioning policy — what triggers patch/minor/major, and
how model and eval versioning relate to it — is in the `plugin-dev` plugin's `bump-version`
skill. This repo's own decisions are in `VERSIONING.md`.



## [0.9.0] - 2026-09-20

Evals become a thing the kit does, rather than a thing each chat improvises. `run-evals` is
the loop; every skill and agent gets a committed set that outlives the plan that created it;
`plan-phases` specifies each phase's evals against it and `run-phase` runs them and stops for
your review. Planned and built with `plan-phases`/`run-phase` themselves — the design set is
`site/notes/0.9-evals-*.md`, one commit per phase, each with its evals beside it.

### Added
- **`run-evals`, an automatic skill: the eval loop** (5fdfdd9). One target, one committed set,
  one iteration. Mechanical checks, then a load check, then behavioral runs — the working tree
  and a baseline in parallel, each writing `outputs/` and a `transcript.md`, one grader per run
  quoting evidence per assertion, a benchmark and the viewer. The grader, benchmark, viewer and
  trigger scripts are skill-creator's, found where they are installed, with an inline fallback
  that says so in the log when they are not. `references/eval-kinds.md` is the one list of the
  five kinds (`mechanical`, `load`, `behavioral`, `trigger`, `platform-fact`);
  `scripts/eval_workspace.py` lays out the workspace skill-creator's scripts expect. Evals:
  `evals/2026-09-19-run-evals-platform-facts.md`,
  `evals/2026-09-19-run-evals-first-loop.md`.
- **Committed eval sets, one per target** (5fdfdd9, c76777a). `evals/sets/<target>.json` holds
  each eval's prompt, expectations, baseline and scripted-answer sheet, with `added_in` naming
  the change that added it, so the next change to that target reruns it as regression.
  `eval_workspace.py validate` enforces the shape.
- **Trigger evals and a guarded description optimizer** (29b317b). For a skill the model
  invokes itself, `evals/sets/<target>.trigger.json` measures how often its description is
  picked for queries that should invoke it and left alone for near-misses. `run_loop` may
  rewrite a description below 0.9, and its best is applied only under a guard: the held-out
  score must beat the current one, every outside-a-plugin query must still not trigger, and the
  description's scoping clause must survive. Evals:
  `evals/2026-09-19-trigger-sets-validate.md`,
  `evals/2026-09-19-trigger-rates-automatic-skills.md`.
- **Blind comparison for a changed target** (2f256ed). When both configurations pass everything
  the pass rates stop separating them, so `eval_workspace.py blind` stages each eval's two
  output directories as `A` and `B` in a random order, keeps the key out of every prompt, and
  asks skill-creator's comparator which is better. A loss is reported as a loss. Eval:
  `evals/2026-09-20-blind-comparison.md`.
- **`dev-team` gets eval sets** (71cd13e). `dev-team/evals/sets/{implementer,researcher,documenter}.json`,
  seeded from its own eval logs, so its next change has regression tests to rerun. Eval:
  `dev-team/evals/2026-09-20-implementer-security-review-sets.md`.

### Changed
- **`plan-phases` specifies each phase's evals** (f688731). Every phase note gains an `## Evals`
  table — ID, kind, target, baseline, which evals of the target's set, and the pass bar — and
  the phase-0 commit writes those evals into `evals/sets/`, so a phase arrives with its tests
  rather than inventing them. `references/example-phase.md` is the worked note; the phase
  template follows. Eval: `evals/2026-09-19-plan-phases-evals-table.md`.
- **`run-phase` runs the evals and stops for review** (a0a381f). At the note's Evals step it
  invokes `run-evals` once per target, fixes and reruns once if a bar is missed, records a
  Deviation if it is still missed, and does not commit until you have looked at the outputs.
  `log-eval` entries gain `**Set:**`, `**Iteration:**`, `**Baseline:**`, `**Pass rate:**` and
  `**Trigger rate:**`. Eval: `evals/2026-09-19-run-phase-evals-and-review-gate.md`.

### Verified
- **Both sets rerun end to end against `plugin-dev-v0.8.0`** on the finished branch:
  `plan-phases` 98.5% vs the baseline's 73.5%, `run-phase` 100% vs 85.5%. The difference is
  carried by the two evals this change added — `plan-phases` eval 4 (7/7 vs 0/7) and
  `run-phase` eval 1 (7/7 vs 5/7); the rest is regression cover 0.8.0 also passes. Trigger
  rates on the five automatic skills: 1.00 · 1.00 · 0.90 · 1.00 · 0.95, no description
  changed. Evals: `evals/2026-09-20-end-to-end-0.9.0.md`,
  `evals/2026-09-20-release-checks-0.9.0.md`, `evals/2026-09-20-trigger-rates-rerun.md`.
- **`run-phase` gained one clause the end-to-end run forced.** `run-evals` step 7 requires a
  weak expectation to be corrected in its set "in this change"; `run-phase`'s "only this
  phase's edits" forbade it. The eval sets a phase's own `run-evals` run reads are now
  explicitly in scope for expectation corrections — the target's behavior still is not.

### Breaking
1. `run-phase` now stops before committing when the phase ran a behavioral eval, until the
   user has reviewed the viewer. Mechanical-only phases commit as before.
2. `run-evals`' trigger optimizer may rewrite the `description:` of a skill the model invokes
   itself; each rewrite is logged with the trigger rate before and after.
3. Plugins get a gitignored `evals/workspace/`; new plugins get it from the template.
4. `templates/phases/phase.md` gains a `## Evals` section; notes written before 0.9 still run.

## [0.8.0] - 2026-09-19

### Changed
- **`plan-phases` composes jobs into shared layers before it proposes** (72712ec). A new
  *Compose the workflows* step designs from the unit of work a practitioner reads one at a
  time: per-unit agents fanned out in parallel (extract), one status file per entity that
  every job reads (synthesize), a comparison against peers or baseline that is core by
  default (compare), and thin typed commands on top (act). Agents are methods shared across
  jobs; the proposal states each job's first-run and warm-run cost and each shared file's
  rules (what it cites, never claims, when it goes stale). Suggestions attach and never
  carry the core; components are labelled *asked*, *composed* or *suggested*.
- **The proposal is a page, not code in chat.** Published as an Artifact with the flow
  chart rendered; the page declares UTF-8 and loads mermaid from cdnjs with a
  theme-aware, full-size init, so it also renders as a downloaded file. The chart is
  budgeted to about 20 nodes and 30 edges, grouped by layer. README and both phased
  workflow pages follow. Eval: `evals/2026-09-19-plan-phases-compose-layers.md`.

## [0.7.0] - 2026-09-19

### Changed
- **`plan-phases` expands the idea before it plans** (1e0b2a0). It reads first, then
  interviews in themed rounds of 2–4 questions (recommendation first, each round built on the
  last answers) until every component can be named. It then shows a proposal in chat — the
  idea restated, a mermaid flow chart of every command, skill, agent and file, a components
  table, decisions, a phase outline, non-goals — with its own suggested additions dashed and
  accepted or rejected by name. No branch, scaffold or file exists before the user approves;
  the approved proposal becomes the overview. `templates/phases/overview.md` gains an Origin
  column under Decisions taken and a line for declined suggestions under Non-goals; the
  README and both phased workflow pages follow. Eval:
  `evals/2026-09-19-plan-phases-interview-and-approval.md`.

## [0.6.0] - 2026-09-18

### Added
- **`plan-phases`** — a typed skill that splits a change too big for one chat into phases: a
  branch, `site/notes/<slug>-00-overview.md`, one note per phase with its own evals, and a
  progress ledger, committed as phase 0. `--new <name>` from the repo root starts a whole
  plugin the same way, with `new-plugin`'s scaffold as its phase 0. Templates in
  `templates/phases/`.
- **`run-phase`** — a typed skill that does the next unfinished phase in a fresh chat: exactly
  that note's edits, the checks, the phase's evals logged, one commit, the ledger updated, then
  stop.
- **`plugin-dev`'s own `contracts.yml`** — no bare `/<name>` command in the bundle, the README's
  skills table names every skill, and every typed skill is in `site/site.yml`'s run order. Each
  claim watched fail on a planted defect: `evals/2026-09-18-phases-skills-contracts.md`.
- **`site/`** — the bundle's reading site, with three workflow pages (small change, phased
  change, new plugin) that the README summarizes.

### Changed
- `new-plugin` hands a plugin with agents, or more than a couple of skills, to
  `plan-phases --new` after the scaffold instead of writing it in the same chat.
- The root `CLAUDE.md` and the plugin `CLAUDE.md` template describe the two typed skills, and
  the root `CLAUDE.md` gains *Working in one plugin*: stage by plugin path, never `git add -A`,
  and commit-bearing steps run in Claude Code, not Cowork.

## [0.5.0] - 2026-09-17

### Added
- **`near: <n>` on a `forbid` claim** — scopes `all_of` and `unless` to the matched text plus n
  characters either side instead of the whole line. Almost every exemption means "this occurrence
  is fine", not "this line is exempt", and an exemption lives exactly where the thing it pardons
  is discussed — which is where a violation would be written. `dev-team`'s `scripts/` claim, the
  oldest in the repo, had eight line-scoped exemptions pardoning ten lines outright: a genuine
  `scripts/` promise planted on any of them passed. Eleven of eleven planted violations leaked
  before, all eleven caught after, with the legitimate lines still silent —
  `evals/2026-09-17-forbid-exemption-scope.md`. One residual is documented rather than hidden: a
  violation inside the window, in the same clause as its exemption, is still pardoned.
- `check-contracts` states the scoping rule first among the three things to know about writing a
  claim, with both tighter options (a smaller window, or a negative lookahead in the pattern,
  which exempts a token and has no window), and says plainly that a claim nobody has watched fail
  is not enforcement — adding or changing one means planting the defect and running `log-eval`.

### Fixed
- **A skill's `references/*.md` was always filed under *Knowledge skills*,** whatever kind of
  skill owned it, so `dev-team`'s `shape-brief / brief` sat six entries away from
  `/dev-team:shape-brief` — while the page itself was written to `skills/workflow/`. A reference
  file is now listed with its owner, directly after it. Filing a workflow skill's reference under
  Knowledge separates the page from the only thing that explains it, and implies an agent reads
  it on its own.
- **`site_title` defaulted to the plugin's name with hyphens replaced by underscores,** so
  `dev-team` rendered as `dev_team`. It defaults to the name as written. This was the source of a
  wrong spelling that looked bundle-local; `dev-team` has dropped the explicit `site_title` it
  needed as a workaround, which is what proves the default.

Nav diffed across both bundles before and after — three changed lines in `dev-team`, one in
`plugin-dev`, each accounted for:
`evals/2026-09-17-build-site-reference-placement.md`.

## [0.4.0] - 2026-09-17

### Added
- `names_listed` gains **`form`** — how the target list cites a name, so a list is checked where
  it lives rather than reformatted to suit the checker. `code` (backticks, the default) for
  prose and tables, `tree` for an indented `── name/` branch in a fenced directory tree where
  backticks would render literally, `list` for a YAML sequence or Markdown bullet.
- `names_listed` gains **`where`** — which directories the list answers for, read from their
  `SKILL.md` frontmatter. A list covering one class of skill is checked against that class, so a
  knowledge skill is not reported missing from a list of workflow steps and a second list of
  which skills count never has to exist. A `where` that matches nothing is a `FAIL`, not
  `0 names, all listed`: a typo would otherwise switch the claim off while still printing PASS.
- `skills/**/*.py` joins the default authored set. A script a plugin ships is authored too, and
  it is the one file that prints to a person rather than to a model — which is how `dev-team`'s
  `status.py` was found printing unnamespaced commands.

### Changed
- `check-contracts` documents both keys, with a table for `form`, and states the line-level
  `unless` hazard as a design rule rather than a formatting caveat: one exempt phrase pardons
  everything else on its line, and an exemption tends to live exactly where the thing it pardons
  is discussed. Prefer a negative lookahead in the pattern, which exempts a token.

### Fixed
- `form: list` anchored a bullet to end-of-line, so a YAML entry with a trailing comment read as
  missing. The checker was fixed rather than the comment removed: a claim that dictates how the
  file it checks may be annotated will be worked around.

Tested, 15 cases over two rounds —
`evals/2026-09-17-contract-sweep-names-listed-where-form.md`. Round 1 found `dev-team`'s D2, D3
and D5; round 2 exists because round 1 tested the command claim with a bare command alone on its
own line, which is not how one gets written, and so missed the `unless` leak above.

## [0.3.0] - 2026-09-17

### Added
- `check-contracts` + `scripts/contract_sweep.py` — checks the cross-file claims a bundle's own
  prompts act on, which nothing else in a plugin verifies: a heading one file parses against
  the template another owns, a rule one file states and another contradicts, a list of names
  that goes stale when a directory changes. Config-driven like the site builder: each bundle
  declares its claims in its own `contracts.yml`, absent means nothing is checked. Owner
  templates are parsed out of the owner file rather than restated, so renaming a heading moves
  the check with it. Exit 0 all pass, 1 any fail, 2 nothing declared.
- Verified against planted defects, one per check kind —
  `evals/2026-09-17-contract-sweep-negative.md`. Two lessons about writing claims (a broad
  `unless` becomes an escape hatch; the checks are line-based, so an exemption phrase must fit
  on one line) are written into the skill.

### Changed
- `CLAUDE.md` carries the shared-script rule for `contract_sweep.py` alongside the one for
  `build_site.py`: a change to it gets both runs — the real bundle, which must still pass, and
  a defective copy, which must still fail.

## [0.2.0] - 2026-09-17

### Changed
- `scripts/build_site.py` — a skill only a person can start
  (`disable-model-invocation: true`) is now a **Workflow skill**, not a Knowledge skill.
  A step that runs inline in the conversation rather than forking into an agent was being
  filed as material an agent reads, and its `workflow_skills_order` entry had no effect.
  `dev-team` rebuild: `status` and `shape-brief` moved into Workflow skills, 48 pages.
- `build-site` — the run command now has a fallback for sessions where the plugin is not
  installed (`CLAUDE_PLUGIN_ROOT` unset): `python3 ../plugin-dev/scripts/build_site.py`.

## [0.1.0] - 2026-09-16

### Added
- `build-site` skill and `scripts/build_site.py` — the generic site builder, extracted from
  `dev-team/site/build_site.py` and de-hardcoded. Verified byte-identical against
  `dev-team`'s existing site; see `evals/2026-09-16-build-site-extraction.md`.
- `bump-version` skill — the semver, CHANGELOG, tag and marketplace procedure, plus the
  `model:` field policy, extracted from `dev-team/VERSIONING.md`.
- `log-eval` skill — the eval record convention, extracted from `dev-team/evals/README.md`.
- `new-plugin` skill and `templates/` — scaffolds a plugin as a subdirectory of this repo.
