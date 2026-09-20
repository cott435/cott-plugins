# `run-evals` blind comparison — `eval_workspace.py blind` and 0.8 vs 0.7 un-blinded

**Tested against:** uncommitted — see working-tree diff (`skills/run-evals/scripts/eval_workspace.py`, `skills/run-evals/SKILL.md`) · model: `claude-opus-5` · 2026-09-20
**Set:** `evals/sets/plan-phases.json` evals 1, 2, 3 · **Iteration:** `evals/workspace/plan-phases/iteration-1` · **Baseline:** `plugin-dev-v0.7.0` (`25a018f`) · **Pass rate:** 45/48 vs 12/48 (phase 1's graders; no new executor runs) · **Blind:** new preferred 3/3

## What was tested

Two claims from 0.9-evals phase 5. **P5-M1:** `eval_workspace.py blind` stages both
configurations of every eval in an iteration as `blind/A` and `blind/B` in a random order,
records which is which in `blind/key.json`, and leaks no path to that key in what it prints.
**P5-B1:** un-blinded, skill-creator's comparator prefers `plan-phases` 0.8 over 0.7.0 on at
least 2 of the 3 evals — the question assertions cannot answer, since a set can only say
both sides passed.

## Method

**P5-M1** — mechanical, on a copy of `iteration-1` in the session scratchpad (outside any
plugin root, which also exercises the `expected_output` fallback). One run checked the tree
and the printed JSON; four further runs checked that the A/B assignment actually varies; one
run against an empty directory checked the no-pairs path. No model involved.

**P5-B1** — three general-purpose subagents, one per eval, in one message, each given
`skill-creator/agents/comparator.md` (marketplace checkout at
`~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator`)
and nothing but `a_dir`, `b_dir`, the eval prompt, its 16 expectations and the set's
`expected_output`, plus an instruction to read nothing else under the iteration. No new
executor runs: this reuses the `run-1` outputs phase 1 produced, so the only cost is the
three comparators (~250k tokens total, ~90s each). The key was read only after all three
verdicts were written. `with_skill` is the working tree's `plan-phases` (0.8); `old_skill` is
the `plugin-dev-v0.7.0` snapshot.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| P5-M1 A/B dirs and key | `blind/A`, `blind/B`, `blind/key.json` for every eval; A/B contents match the config the key names | 3/3 evals, contents matched | ✅ |
| P5-M1 no key leak | printed list contains no path to `key.json` and no key field | keys printed: `a_dir`, `b_dir`, `eval`, `expectations`, `expected_output`, `prompt` | ✅ |
| P5-M1 order is random | A is not always the same configuration | 5 runs: `old/new/new`, `new/new/new`, `old/old/old`, `new/new/old`, `old/new/old` | ✅ |
| P5-M1 nothing to compare | an iteration with no complete eval is an error, not a silent success | prints `[]`, exits 1 | ✅ |
| P5-B1 eval 1 trading | comparator prefers the newer version | winner B = `with_skill`; rubric 10.0 vs 5.7; its own expectation count 16/16 vs 3/16 | ✅ |
| P5-B1 eval 2 ml-papers | comparator prefers the newer version | winner A = `with_skill`; rubric 10.0 vs 5.0; 16/16 vs 5/16 | ✅ |
| P5-B1 eval 3 support-tickets | comparator prefers the newer version | winner B = `with_skill`; rubric 10.0 vs 5.3; 16/16 vs 4/16 | ✅ |
| P5-B1 bar | newer version preferred on ≥ 2 of 3 | 3 of 3, no ties | ✅ |

## Verdict

Both claims held. The tally is in `iteration-1/benchmark.md` under `## Blind comparison`, and
the per-eval verdicts in `eval-*/blind/comparison.json`.

Four things the run says about the instrument, not about `plan-phases`:

1. **The label varied and the verdict did not.** `with_skill` was A once and B twice, so the
   3/3 is not a position bias. This is the check worth repeating whenever a comparison looks
   unanimous.
2. **The two sides differ in format** — `proposal.html` against `proposal.md` — because
   publishing a page *is* part of what 0.8 changed. The comparator cannot know which version
   is which, but that tell is systematic across all three evals, so the three verdicts are
   correlated: this is one finding with three witnesses, not three independent ones. A
   comparison between two versions that produce the same file shapes is the stronger test,
   and 0.9's own later targets will be that.
3. **The comparator's own expectation counts are not the graders'** — 48/48 vs 45/48 for the
   new side. It re-checks independently and treats assertions as secondary evidence; eval
   3's comparator recorded that neither directory had a `chat.md`, so the "no raw mermaid
   fence in chat" expectation could not be checked and it scored it passing for both. That is
   the same `chat.md` gap phase 1 noticed in this set — the executor prompt never asks for
   one — and it is still unfixed in `evals/sets/plan-phases.json`.
4. **This is a weak instance of the case the feature exists for.** The trigger rule fires
   when both sides pass everything or the rates are within 10 points; here they were 33 points
   apart, so the comparison was run because the phase note asked for it. It proves the
   mechanism end to end, not that the comparator can separate two *good* versions — the first
   real test of that is the first phase whose assertions come out level.
