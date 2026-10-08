# prior-issues loop phase 7 — run-auditor writes P verdicts (B7.1); audit-run checks prior fixes (B7.2) and still audits as before (B7.3)

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `6974d1e`): `agents/run-auditor.md`, `skills/audit-run/SKILL.md`, `skills/run-flow/scripts/trace.py`, `skills/run-flow/scripts/flow.py` · model: executors and graders `claude-sonnet-5-5` (Agent tool `model: sonnet`); the auditors the audit-run executors spawned were general-purpose agents on the same model · 2026-10-07
**Set:** `evals/sets/run-auditor.json` evals 1, 2 (B7.1); `evals/sets/audit-run.json` evals 6 (B7.2), 2 (B7.3) · **Iteration:** `evals/workspace/run-auditor/iteration-1` (B7.1); `evals/workspace/audit-run/iteration-5` (B7.2, B7.3); `evals/workspace/audit-run/iteration-6` (B7.2 after the harness fix) · **Baseline:** previous = `359f45e` (`old_skill`) for all · **Pass rate:** B7.1 with_skill 16/16 (100%) vs old_skill 11/16 (eval 1 9/9 vs 4/9; eval 2 7/7 vs 7/7); B7.3 with_skill 8/8 vs old_skill 8/8; B7.2 iteration 5 with_skill 11/13 graded (the grader dropped one of 14) vs old_skill 0/14, iteration 6 with_skill 14/14 (100%) vs old_skill 0/14 · **Blind:** not run (every pair 28 points or more apart, or a regression row whose two sides both pass)

## What was tested

That run-auditor, given `Prior issues`, writes one `P` line per issue in order (TO-001
`recurred` at U01.S3, TO-002 `not exercised`), files no F finding for the recurrence, and
returns the `· prior …` counts, while with `Prior issues: none` it is unchanged (B7.1); that
audit-run settles per issue whether the fix ran (TO-001 by version, TO-002 not testable),
gives the writer's auditor only TO-001, writes both Checks lines, the report's Prior issues
table and Totals, counts `2 checked`, and files no second issue for the recurrence (B7.2);
and that audit-run's auditors still find the five planted defects (B7.3).

## Method

- `run-evals` behavioral loop; one run per configuration; Sonnet 5.5 executors and graders
  (skill-creator's `grader.md`). Fixture: `evals/fixtures/audit-run/make_session.py` into a
  `mktemp -d` per run.
- **Void and rerun (iteration 5, eval 6, with_skill):** the executor spawned the auditors as
  `plugin-dev:run-auditor`, which loads the installed 0.15.0 agent, not the plugin root's,
  breaking the executor prompt's "use the copy under that directory and no other copy". Its
  U01 auditor wrote no P line twice. The run was voided (kept at
  `evals/workspace/audit-run/void-iteration-5-eval-6-with_skill/`) and rerun after the harness
  `ledger-prior-issues.md` gained the line `auditors-on-fixture.md` already had: spawn them as
  general-purpose agents told to follow `<plugin root>/agents/run-auditor.md`. The rerun's
  six spawns were all `general-purpose`.
- **The one fix (iteration 6):** iteration 5's rerun missed two transcript expectations
  because its `transcript.md` summarised the auditor blocks and the `issues.py new` commands.
  `ledger-prior-issues.md` now requires every shell command and every auditor block verbatim
  in `transcript.md` (the phase 4 harness's wording). In the same pass, audit-run §5 step 4
  gained a sentence: a different F finding matched to a recurred issue is an ordinary `seen`
  and counts in `seen again` (iteration 5's executor had left one out of the count). And
  `audit-run.json` eval 6's expectation on other issue files, which the old_skill grader called
  vacuous when no issue files exist, now also requires at least one new issue file. Eval 6
  was rerun in both configurations as iteration 6.
- **Old-skill rerun (iteration 6):** the first old_skill executor ended with no
  `transcript.md`: its Write of `.md` files was refused ("Subagents should return findings as
  text, not write report files"). Voided (outputs kept at
  `evals/workspace/audit-run/void-iteration-6-eval-6-old_skill/`) and rerun once; the rerun
  wrote its transcript, and that refusal again blocked only its `report.md`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| B7.1 eval 1 with_skill | P lines TO-001 recurred · U01.S3, TO-002 not exercised; no F for the scratch write; return with `· prior 0 held, 1 recurred, 1 not exercised` | as expected; 4 ERROR, 0 WARN, 2 NOTE, none citing U01.S3 | 9/9 |
| B7.1 eval 1 old_skill | fails at least one | ignored the field: no P lines, the scratch write an ERROR, no prior part | 4/9 ✓ |
| B7.1 eval 2 (`Prior issues: none`) | unchanged on both | no Prior issues section, no prior part, P1–P4 ERRORs | 7/7 and 7/7 |
| B7.2 eval 6 with_skill, iteration 5 | every expectation | auditor blocks and `issues.py new` commands not shown in the transcript | 11/13 |
| B7.2 eval 6 with_skill, iteration 6 | every expectation | TO-001 testable by version, TO-002 `fixed_in blank`; U01 block carries TO-001 only, seg-1 `none`; Prior issues table two rows; Totals `prior: 0 held, 1 recurred, 0 not exercised, 1 not testable`; commit message `… 2 checked`; `issues.py check` ok | 14/14 |
| B7.2 eval 6 old_skill | fails at least one | never reads the ledger | 0/14 (both iterations) ✓ |
| B7.3 audit-run eval 2 | every expectation (regression) | P1–P5 found, one-line returns | 8/8 (old 8/8) |

Graders' notes on the sets, not acted on: run-auditor eval 1 could assert the ERROR count;
eval 6's TO-002 evidence expectation could quote the `fixed_in blank` the skill writes; the
iteration-6 run filed a WARN as an issue whose own text says nothing needs fixing (TO-009),
which no expectation covers; run-auditor eval 2's harness does not copy the driver trace for
citation checks.

## Verdict

Held: B7.1, B7.2 (iteration 6) and B7.3 meet their pass bars. B7.2 needed one void rerun (an
executor that loaded the installed agent) and one fix, all in the eval harness plus one
counting sentence in audit-run; the rerun confirmed it at 14/14.
