# review-plugin, plan-phases from an edit list, run-phase writing its own note

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-review-plugin` over `b3782e9` (`skills/review-plugin/`, `skills/plan-phases/SKILL.md`, `skills/run-phase/SKILL.md`, `scripts/edits.py`, `templates/review/`, `templates/phases/`) · model: executors and graders `claude-sonnet-5-5` (Agent tool `model: sonnet`); orchestrating chat Opus 5.5 · 2026-10-09
**Set:** `evals/sets/run-phase.json` evals 3, 4 · `evals/sets/plan-phases.json` eval 3 · `evals/sets/review-plugin.json` eval 1 · **Iteration:** `evals/workspace/{run-phase,plan-phases,review-plugin}/iteration-1` · **Baseline:** `b3782e9` for run-phase and plan-phases; none for review-plugin · **Pass rate:** run-phase 100% vs 80%; plan-phases 100% vs 9%; review-plugin 100% vs 0%

## What was tested

That a sweep across a plugin can go review → edit list → phases without one chat reading
everything: `review-plugin` orchestrates unit agents and a reconcile agent while reading only
script output; `plan-phases` plans from an edit list through `edits.py` and writes no phase
note; `run-phase` writes its phase's note from the overview and the files as they are, and
finds an item's cited line where earlier phases moved it.

## Method

Real runs, one per configuration, on the toy fixture (`evals/fixtures/toy-plugin/`, with the
new `site/notes/fix/` review plan whose E-002 line moved from 8 to 14). Executors ran the
target file in a temp git copy; graders were skill-creator's `grader.md`. Blind comparison
not run: every pass-rate gap is over 10 points.

Mechanical, by hand:
- `contract_sweep.py` on the bundle: 15/15 pass. A copy with `## Needs a design` and
  `## Evals by phase` renamed in their templates: the two new claims FAIL, 13/15.
- `edits.py findings` on `dev-team/site/notes/determinism/findings/` (13 files, 317
  findings): all parse, no FAIL.
- `edits.py check --findings` on the determinism `10-reconciled.md`: 0 findings uncited; FAILs
  only on the format the list predates (no `Decisions taken` or `Build order` section, eight
  DECIDE items without a `decide: D-nn` field).
- `edits.py` negatives, each FAILs: a dependency cycle; an open decision under `--decided`;
  DECIDE without a D-id; an item in two phases; an unknown id; an item whose dependency is in
  a phase its own phase does not depend on. `coverage` and `check --decided` on the toy `fix`
  plan: ok.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| run-phase 3, note written at phase start | note from the template, overview's eval rows copied, before the edit, one commit | with 8/8; old 6/8 (old wrote a note in its own shape: no Decisions, Specification, Done when) | yes |
| run-phase 4, moved lines | `edits.py show --phase 2`, line 14 cited, only E-002 made | with 7/7; old 6/7 (read the whole edit list; placed the line right) | yes |
| plan-phases 3, from an edit list | `edits.py check/index/coverage`, Items per phase, Evals by phase, no note | with 11/11; old 1/11 (stopped: no design) | yes |
| review-plugin 1, toy sweep with a planted contradiction | plan, 2 units in one message, REC, `edits.py` checks pass, item for `waved.log`, orchestrator reads no bodies | with 9/9 (9 items, 2 decisions); without 0/9 (found it, edited the plugin directly) | yes |
| mechanical, above | each check passes on good input, fails on planted defects | as expected | yes |

## Verdict

Held. Caveats: executor transcripts are prose summaries, so "never read whole" and "spawned in
one message" rest on the executor's account. The harness sheets for run-phase 3 and 4 told the
baseline what to do (a missing note "the target must write"; the line "now line 14"), so the
old skill's 6/8 and 6/7 overstate it; both hints removed after the run, not rerun. plan-phases
3's harness left `greet` in its post-phase-1 state; it now resets it.

Set edits after this iteration: run-phase 3 expectation 5 reworded (a "must not touch" line is
not a Files row); review-plugin 1 gained "no commit changes `skills/` or `CLAUDE.md`".

Not run: plan-phases 1–2 (expectations rewritten for overview-only output), run-phase 1–2,
run-phases 1, design-plugin (fixture paths updated only). The executor hit the zsh
variable-command failure once (`edits.py` from a variable) and recovered.
