# `run-phase` eval 1's review-stop assertion — made able to fail, and shown failing

**Tested against:** uncommitted — see working-tree diff (`evals/fixtures/toy-plugin/site/notes/0.2-progress.md`, `evals/fixtures/toy-plugin/site/notes/0.2-01-farewell.md`, `evals/sets/files/run-phase/review-approve.md`, `evals/sets/run-phase.json`); `skills/run-phase/SKILL.md` unchanged at `21437d6`; baseline `plugin-dev-v0.8.0` → `bab28b8` · model: `claude-opus-5` (both executors fell back to `claude-sonnet-4-5` for their own nested subagents — same on both sides) · 2026-09-20
**Set:** `evals/sets/run-phase.json` eval 1 · **Iteration:** `evals/workspace/run-phase/iteration-3` · **Baseline:** `plugin-dev-v0.8.0` (`bab28b8`) · **Pass rate:** 8/8 = 100% vs 5/8 = 63%

## What was tested

The defect the 0.9.0 end-to-end run found and did not fix
(`2026-09-20-end-to-end-0.9.0.md`, and note 07's Deviations): eval 1's review-stop
assertion could not fail. The fixture itself mandated the stop — its ledger's Standing facts
said "stopping for review when a row is behavioral" and the note's Done-when said "T1-B1
logged **and reviewed**" — so an executor stopped whichever version of the skill it had
read, and 0.8.0, which has no review gate at all, passed that assertion. The claim under
test now: with the mandate removed, the assertion passes for 0.9 and **fails** for a version
with no gate.

## Method

Real runs, through `run-evals`. Four changes, then eval 1 rerun on both configurations, one
run each, graded by skill-creator's grader:

1. `0.2-progress.md` — the review clause struck from Standing facts.
2. `0.2-01-farewell.md` — Done-when is now "T1-B1 logged".
3. `review-approve.md` — the harness captures `git log --oneline` into
   `outputs/git-log-at-review.txt` **at the moment** the review question is asked, and is
   told the fixture does not ask for a stop and not to prompt for one.
4. `run-phase.json` eval 1 — the old assertion replaced by two: the stop is attributable to
   the target alone (FAIL if no review question was asked), and
   `git-log-at-review.txt` exists and holds only `fixture`, not the phase commit (FAIL if
   absent, or if the phase commit is already in it). 7 expectations → 8.

The fixture now contains no occurrence of "review" at all; both graders were told to verify
that with `grep` themselves before judging, and both did.

## Results

| Expectation | `with_skill` (0.9) | `old_skill` (0.8.0) |
|---|---|---|
| 1 `run-evals` invoked, iteration dir created | PASS | **FAIL** — not in the 0.8.0 bundle; hand-built harness, no `evals/workspace/` on disk |
| 2 stopped for review on its own initiative | PASS | **FAIL** — `interview.md`: "The target asked the executor nothing" |
| 3 stop came before the commit | PASS — `git-log-at-review.txt` is `8e07110 fixture` alone | **FAIL** — file absent |
| 4 exactly one new commit | PASS — `a10bb48` | PASS — `154ae6e` |
| 5 commit contents | PASS | PASS |
| 6 ledger row `done`, logs named | PASS | PASS |
| 7 nothing pushed, no tag | PASS | PASS |
| 8 `evals/workspace/` not in commit | PASS | PASS (vacuously — no such directory existed) |
| **Total** | **8/8 = 100%** | **5/8 = 63%** |

## Verdict

**The claim held, and the evidence is a real failure rather than an argument.** The two new
assertions are demonstrably capable of failing: 0.8.0 failed both. Its own executor stated
why — the skill goes eval → `log-eval` → "One commit" with no approval point in between, so
the harness's approval answer was never requested and the phase commit lands before any
result reaches the user. Under the old fixture that same behaviour scored the review
assertion as a pass.

Assertion 3 closes the second half of the grader's critique from the 0.9.0 run: a target
that committed first and asked afterwards used to pass, and now cannot, because the log is
captured at the question rather than reconstructed from the end state.

The comparison moved from 7/7 vs 5/7 to 8/8 vs 5/8. The baseline's 5 remaining passes are
genuine — it does produce one correct commit with the right contents, ledger row and logs —
which is the right outcome: 0.8.0 is not broken, it simply has no review gate and no
`run-evals`.

**Not fixed here, still `*noticed:*`.** Both graders flagged again that expectation 8 gives
the baseline a free point (it passes precisely because `run-evals` never ran — pair it with
a positive check that the workspace exists on disk but is untracked), and that expectation 7
cannot fail while the fixture has no remote. The `old_skill` grader added a new one: nothing
scores the most creditable thing that run did — disclosing the missing-`run-evals`
substitution in three committed places (the note's `## Deviations`, the eval log's Method,
the ledger's Notes) instead of skipping silently.

**Corroboration of a 0.9.0 change, unplanned.** The `with_skill` run exercised the carve-out
phase 7 added to `run-phase`: it acted on its own graders' step-7 critique by tightening
`evals/sets/farewell.json` eval 1 inside the temp copy, rather than demoting it to a
`*noticed:*` line as both phase-7 runs had to. No verdict changed and nothing was rerun.
