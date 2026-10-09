# designer: module-size floor

**Tested against:** `8895dcf` (`agents/designer.md`, `skills/project-structure/SKILL.md`, `agents/implementer.md`) · model: executors, graders and comparators all `claude-sonnet-5-5` (Agent tool `model: "sonnet"`; the designer's own `model:` is `inherit`) · 2026-10-09
**Set:** `evals/sets/designer.json` evals 14, 15 (both new in this change) · **Iteration:** `evals/workspace/designer/iteration-2` · **Baseline:** `0f99e7b` (the commit before the floor; `previous` would have been HEAD, which already carries it) · **Pass rate:** 100% vs 94% · **Blind:** new preferred 1/2

## What was tested

The designer sizes its Module plan from below as well as above: a small section's files are folded into the sibling they overlap, unless one is a definitions or config file, an entry point, or owns a responsibility alone, and a large section is not collapsed.

## Method

Real runs, one per configuration per eval (4 executors, 4 graders, 2 blind comparators), all designer mode `new` against the `repo-planned` fixture: eval 14 is `data/clean`, a small section; eval 15 is `data/storage`, a large one, as the guard. `with_skill` is the working tree at `8895dcf`; `old_skill` is a snapshot at `0f99e7b`. The implementer's half of the change (note an undersized module, do not merge it) and the reviewer's (not a finding) were **not** exercised: they need a built section, and no eval here builds one. `benchmark.md`'s "3 runs each" and time/token spreads are the aggregator's, over one run each.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 14 `clean`, with floor | one or two logic modules, a reason for any file under ~100 lines | `errors.py` + one `cleaning.py` (~90 lines) holding the checks and the duplicate rule, reason given under the table | 8/8, expectation 4 a marginal pass (90 lines, reason beside the plan, not on its line) |
| 14 `clean`, baseline | the old behaviour: a file per concern | `errors.py`, `checks.py` (~60), `cleaning.py` (~70), no reason for either; only "far below the 400-line soft limit" | 7/8, fails expectation 4 |
| 15 `storage`, with floor | not collapsed | `errors.py`, `configs.py`, `store.py` ~130, `bars.py` ~200, `runs.py` ~180 | 8/8 |
| 15 `storage`, baseline | not collapsed | `errors.py`, `configs.py`, `schema.py` 110, `bars.py` 170, `runs.py` 170 | 8/8 |
| Blind 14 | prefer the floor | with floor preferred, 9.7 vs 8.0 | win |
| Blind 15 | tie or win | baseline preferred, 9.0 vs 8.0, both passing all five of the comparator's expectations; on helper placement and versioned migrations, not on module size | loss |

## Verdict

The floor does what it was written to: on a small section the designer folded two modules into one and said why, where the baseline planned two files of 60 and 70 lines; on a large section both configurations kept the split, so the floor did not over-collapse it. That is one sample per cell, a single small section, and a fold to ~90 lines that only just clears "about 100".

The blind loss on eval 15 is reported as a loss. Both plans met every expectation and the size floor, so it does not bear on the floor, but a single run cannot rule out that the floor's extra text nudged the design. Not rerun.

Changes made to the set from the graders' critique, none regraded: eval 14 expectation 4 now says where the reason may sit and that a ~60-70 line module with none fails; the agent-memory path in both accepts `dev-team-designer/`; eval 15 gained an expectation that every logic module is estimated at ~100 lines or more (both iteration-2 plans meet it by their own estimates, but no grader scored it). A further suggestion, an expectation that the design's prose module counts match its own plan (eval 15's with-floor design says "four modules" for a plan with three), is not added. Untested: the implementer note and the reviewer rule.
