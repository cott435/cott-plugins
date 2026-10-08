# release phase 9 — the audit → ledger → rerun loop end to end: audit-run (B9.1), run-flow (B9.2), run-auditor (B9.3), Sonnet 5.5

**Tested against:** the targets as committed — `skills/audit-run/SKILL.md` `dd6af0f`, `agents/run-auditor.md` `dd6af0f`, `skills/run-flow/SKILL.md` `fe86085`, `skills/run-flow/scripts/trace.py` and `flow.py` `dd6af0f` — on branch `plugin-dev-0.16-audit-ledger`, with phase 9's uncommitted docs and the run-flow harness change in the working tree (see working-tree diff) · model: executors and graders `claude-sonnet-5-5` (Agent tool `model: sonnet`) · 2026-10-07
**Set:** `evals/sets/audit-run.json` evals 2, 5, 6 · `evals/sets/run-flow.json` evals 1, 2, 3 · `evals/sets/run-auditor.json` evals 1, 2 · **Iteration:** `evals/workspace/audit-run/iteration-7`, `evals/workspace/run-flow/iteration-6` (supersedes `iteration-5`), `evals/workspace/run-auditor/iteration-2`; viewers `review.html` in each · **Baseline:** audit-run and run-auditor `previous` = `359f45e` (`old_skill`); run-flow `none` (`without_skill`) · **Pass rate:** audit-run with_skill 35/38 (92%) vs old_skill 8/38 (21%); run-flow with_skill 22/23 (96%) vs without_skill 9/23 (39%); run-auditor with_skill 16/16 (100%) vs old_skill 11/16 (69%) · **Blind:** not run (both `old_skill` targets differ from their baseline by more than 10 points, and not every expectation passed in both)

## What was tested

That the loop the release ships works in sequence on the fixture: an audit files each planted
defect once as a ledger issue with a report under `audits/runs/` and one `audits/` commit
(audit-run eval 5), auditors still find the planted defects (eval 2), a rerun audit checks a
prior fix and writes Checks lines and `P` verdicts (eval 6, run-auditor 1–2), and run-flow
draws any run — by id, by title words with a fork question, and one agent type across two
sessions — as served pages that judge nothing (run-flow 1–3).

## Method

- `run-evals` behavioral loop, one run per configuration; fixture
  `evals/fixtures/audit-run/make_session.py` into a `mktemp -d` per run; harness files as the
  sets name them. Graders: skill-creator's `agents/grader.md`, one per run.
- **run-flow `iteration-5` is superseded.** In it every with_skill executor started no
  server, which `evals/sets/files/run-flow/fixture.md` then allowed, so the closing line had
  no `http://127.0.0.1:<port>` URL (with 20/23, without 9/23). At the coordinator's direction
  the fixture now requires starting the server, checking it answers 200, giving its URL and
  killing it by pid (a Deviation in note 09), and B9.2 was rerun whole as `iteration-6`.
  The expectations are unchanged.
- **Timings missing.** audit-run iteration-7 evals 5 and 6 (all four runs) and every run of
  run-flow iteration-6 have no `timing.json`: their completion notices were not captured, and
  no executor was rerun for a timing. `benchmark.md`'s Time and Tokens rows for audit-run
  therefore average real numbers with zeros and mean nothing; run-flow's are empty.
  audit-run eval 2 and all of run-auditor iteration-2 have real timings.
- **Set correction.** audit-run eval 5's Prior-issues expectation asked for
  `none: no issue had a fix in the code that ran`; audit-run `SKILL.md:274` writes
  `none: no fixed issue to check`, and the grader flagged the disagreement. The expectation in
  `evals/sets/audit-run.json` now reads the skill's line. The run was graded on the old
  wording and is not regraded: its grader quotes the report's line as `none: no fixed issue to
  check`, so it meets the corrected expectation, and eval 5 with_skill is 14/16 against the
  corrected set (13/16 as graded; the pass rates above are as graded).

## Results

| Target · eval | with | baseline | with_skill misses |
|---|---|---|---|
| audit-run 2 auditor-finds-planted-defects | 8/8 | old 7/8 | — |
| audit-run 5 audit-writes-ledger | 13/16 (14/16 on the corrected set) | old 1/16 | see below |
| audit-run 6 audit-checks-prior-fixes | 14/14 | old 0/14 | — |
| run-flow 1 chart-by-session-id | 8/8 | without 1/8 | — |
| run-flow 2 title-words-and-fork-question | 6/7 | without 1/7 | the first `trace.py build` is not shown with `--plugin toy` and `AUDIT_RUN_PROJECTS` |
| run-flow 3 writer-across-two-sessions | 8/8 | without 7/8 | — |
| run-auditor 1 prior-issues-recurred-and-not-exercised | 9/9 | old 4/9 | — |
| run-auditor 2 no-prior-issues-unchanged | 7/7 | old 7/7 | — |

audit-run eval 5 with_skill misses:

1. **Found in quote (real miss).** TO-006's Found in quote is
   `1 failed, 3 passed then commit (U01.S4, U01.S5); D4, D6: free-text Done. …` — step ids
   and paraphrase, not a quote from one step. The transcript shows why: `issues.py` rejected
   the step field `U01.S4, D4, D6` (one finding spanning a unit and the driver), and the
   executor folded the steps into the quote to get past it. The grader also notes TO-002's and
   TO-004's quotes stitch two fragments.
2. **Prior issues wording** — the set's error, corrected above.
3. **`issues.py new` once per file (real miss, partly unverifiable).** The transcript
   abbreviates commands despite the harness, so "every shell command verbatim" is not met;
   and the issue files were not each made by one `new`: TO-006 and TO-007 were deleted with
   `rm` after `issues.py check` failed on them and made again (`new` ran 9 times for 7 files).
   No issue file or `INDEX.md` was edited by hand.

run-flow eval 2 with_skill: the transcript is prose; it shows the title words used first
(`T build with title words: exit 1, two chats match`) and the full id only after the answer,
but never the first call's flags. Iteration 5's with_skill run missed the same expectation the
same way. `fixture.md` asks for a record of what was done but not every command verbatim, as
audit-run's harnesses do.

Grader critiques of the expectations, not acted on in this entry: run-flow eval 1's
command-shape check rests on a transcript that abbreviates commands; run-flow eval 3's "every
unit carries a `mode` key" passes trivially (all null); audit-run eval 5's quote check does not
test that the quote is a substring of the cited step.

## Verdict

B9.3 held: run-auditor 16/16 vs old 11/16. B9.1 and B9.2 missed their bar (every with_skill
expectation passes) on three expectations: audit-run eval 5's Found in quote and its
one-`new`-per-file check, and run-flow eval 2's first-command check. The ledger, the rerun
checks and every chart page held everywhere else, against baselines of 21% and 39%. No fix
has been made yet. The quote miss comes from `issues.py` rejecting a multi-step Found in step
field, which is outside note 09's Files. The other two misses come from transcripts that do
not list commands verbatim.

**Reviewed:** committed with the three misses as a Deviation in note 09 (option a). The
set correction is kept. Follow-ups: let `issues.py new` take a multi-step Found in step,
and make run-flow's `fixture.md` require every command verbatim.
