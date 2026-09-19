# `plan-phases` specifies each phase's evals — regression on the three briefs, the Evals table through phase notes, and the sets it writes

**Tested against:** uncommitted — see working-tree diff (`skills/plan-phases/SKILL.md`,
`skills/plan-phases/references/example-phase.md`, `templates/phases/phase.md`,
`contracts.yml`, and after the P3-M1 failure `skills/run-evals/scripts/eval_workspace.py` and `skills/run-evals/SKILL.md`; branch `plugin-dev-0.9-evals` at `29b317b`). Baseline `old_skill` =
`plan-phases` at the merge-base `bab28b8` (0.8.0) · skill-creator from
`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator`
· model: `claude-opus-5` (executors and graders are general-purpose subagents) · 2026-09-19

**Set:** `evals/sets/plan-phases.json` · **Evals:** 1, 2, 3, 4 · **Iteration:**
`evals/workspace/plan-phases/iteration-2` (gitignored) · **Baseline:** `old_skill` at
`bab28b8` · **Pass rate:** with_skill 54/55 (98%), old_skill 47/55 (85%) — evals 1–3: 47/48
vs 47/48; eval 4: 7/7 vs 0/7

## What was tested

Phase 3 of `0.9-evals` (note `site/notes/0.9-evals-03-plan-phases-evals.md`):

- **P3-B1**: `plan-phases` still designs as well as 0.8.0 on the three committed briefs.
- **P3-B2**: taken through approval, it writes phase notes with an `## Evals` table in
  `run-evals`' kinds, writes the eval sets and harness files in its phase-0 output, and
  states an eval budget in the proposal.
- **P3-M1**: the sets P3-B2 writes pass `eval_workspace.py validate`.
- The contract claim that gains `plan-phases` as a reader.

## Method

- **Contract**: `contract_sweep.py` on the bundle (4/4 PASS). The planted defects were
  `` `smoke` `` added to plan-phases' Kind bullet (the note's check), then
  `**platform-fact**` unbolded in `eval-kinds.md`. Both were reverted.
- **Behavioral**: `init . plan-phases --evals 1,2,3,4` (baseline `previous` → `bab28b8`).
  Eight executors were spawned in one message using run-evals' executor prompt, plus one
  sentence mapping `${CLAUDE_PLUGIN_ROOT}`: the worktree's `plugin-dev/` for `with_skill`,
  the installed 0.8.0 cache for `old_skill` (its `templates/phases/phase.md` is identical to
  `bab28b8`'s). Timing came from each completion notice. There was one grader per run,
  using the grader prompt plus phase 1's sentence (grade expectations naming `chat.md`
  against the transcript's final message). Eval 4's graders were also told which file is
  "the phase-1 note" and "the proposal". `finalize`, then `aggregate_benchmark`.
- **P3-M1**: `validate` on each `evals/sets/*.json` under eval 4 with_skill's `outputs/`.
  Then again on a scratch copy with the four `target_path` files stubbed and a
  `.claude-plugin/plugin.json` added.
- One run per configuration; ~1.59M subagent tokens in total (executors 0.96M, graders
  0.63M).

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Contract, real bundle | all PASS | 4/4; "run-evals names every eval kind…" checks 10 names across 2 readers | ✅ |
| Planted `smoke` in plan-phases' kinds | FAIL | still 4/4 PASS: a reader's `cites` is literal in `contracts.yml`, not read from the file (the limit note 01 recorded) | ❌ |
| `**platform-fact**` unbolded in the owner | FAIL | FAIL, exit 1, naming both `run-evals/SKILL.md` and `plan-phases/SKILL.md` | ✅ |
| P3-B1 eval 1 (trading) | with ≥ 90%, ≤ 1 below old | with 16/16, old 16/16 | ✅ |
| P3-B1 eval 2 (papers) | same | with 15/16, old 16/16. with_skill failed "core stands without suggestions": final phase 7 "Depends on: all", which includes optional phases 5–6 | ✅ (within one) |
| P3-B1 eval 3 (support) | same | with 16/16, old 15/16. old_skill failed "output rules stated" | ✅ |
| P3-B1 overall | with_skill ≥ 90% | 47/48 (98%) vs 47/48 | ✅ |
| P3-B2 eval 4, with_skill | every expectation | 7/7: phase-1 note has `## Evals` with the exact six columns, kinds platform-fact/mechanical/load/behavioral, behavioral row names `evals/sets/research.json` 1 with a numeric bar; 4 sets (11 evals) and 3 files under `evals/sets/files/`; proposal phases table has an "Evals and budget" column (~0.4M … ~2.5M); sections in order | ✅ |
| P3-B2 eval 4, old_skill | fails the Evals-table expectations | 0/7: evals are bullets under Steps, no sets, no budget | ✅ |
| P3-M1, as written | `validate` exits 0 on each written set | exit 1 on all four, each only `target_path 'skills/<x>/SKILL.md' does not exist` | ❌ |
| P3-M1, target files stubbed | exits 0 | exit 0: the schema of all four sets is valid | ✅ (diagnostic) |
| P3-M1 rerun after the `validate` fix, as written | exits 0 | exit 0 on all four, no stubs | ✅ |
| Fix regression: committed `evals/sets/*.json` | exit 0 | exit 0 | ✅ |
| Fix negative: `init` on a set whose target is missing | exit 1 | exit 1 naming the missing `target_path`; no iteration created | ✅ |
| Fix negative: set with emptied expectations and kind `smoke` | exit 1 | exit 1 naming both | ✅ |

## Verdict

**P3-B1 held** (98%, no eval more than one expectation below 0.8.0). **P3-B2 held**: 7/7
against 0/7.

**P3-M1 failed as written, then held after a fix.** This was a design conflict, not a flaw
in the sets. Phase 3 has `plan-phases` write a new target's set in phase 0, before the
target exists, but `validate` (phase 1) rejected any set whose `target_path` was missing.
Every other check passed. On the user's call, `validate_set` gained `require_target`
(default off). `validate` now accepts a missing target, and `init` passes
`require_target=True`, so it still refuses one. `run-evals/SKILL.md` **The set** says so.
The rerun passed as written (exit 0), and the regression and negative cases above held.
The behavioral runs were not rerun, since the fix does not touch `plan-phases`.

**The planted `smoke` defect cannot fail the claim.** The owner side is guarded, but the
reader side still needs a `contract_sweep.py` change.

**The graders' critique of the set**, for its next edit:

- "Core stands without suggestions" needs a rule for a catch-all "Depends on: all" in the
  last phase. That phrase is the only reason with_skill failed eval 2, and eval 3 passed
  the same pattern leniently.
- "Chart and components table agree" checks only table→chart. It should check both ways.
- "Chart is legible" counts nodes and edges but not rendered width; executors saw 1600px
  charts pass.
- "Output rules stated" does not say whether "files readers depend on" includes final
  reports.
- Nothing checks "stopped at approval / no scaffold".
- Eval 4's harness assertion passes vacuously when a set names no files, and never checks
  for an interview `harness` sheet. The sets written here have `harness: null` although
  their targets are typed commands.
- Nothing checks the proposal's budget against the phase note's.
- The `chat.md` wording from phase 1 is still open.
