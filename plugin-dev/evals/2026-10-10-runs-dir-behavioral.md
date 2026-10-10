# runs/ directory, settling and the no-op Checks rule — behavioral sets

**Tested against:** `32f7d7f` (`skills/audit-run/SKILL.md`, `skills/run-flow/SKILL.md`, `skills/fix-issues/SKILL.md`, `skills/bump-version/SKILL.md`, `scripts/issues.py`, `skills/run-flow/scripts/trace.py`) · model: `claude-sonnet-5-5` for executors and graders · 2026-10-10
**Set:** `evals/sets/audit-run.json` evals 2, 5, 6 · `evals/sets/run-flow.json` evals 1–3 · `evals/sets/fix-issues.json` evals 1, 2 · `evals/sets/bump-version.json` evals 1, 2 · **Iteration:** `evals/workspace/{audit-run,run-flow,fix-issues,bump-version}/iteration-1` · **Baseline:** not run (working tree only; `fc80c47` has the old paths the edited expectations no longer name) · **Pass rate:** audit-run 36/38 (94.7%), run-flow 19/23 (82.6%), fix-issues 19/19, bump-version 13/13

## What was tested

With the ledger at `runs/audits/` and a session's trace at `runs/<project>/<command> <title>/<id8>/`, do the four skills that touch them still behave: an audit files issues and writes the report and commit at the new paths, a prior fix is checked and a not-testable one gets no Checks line, run-flow builds and serves from the new workspace, fix-issues and bump-version find and stamp the ledger.

## Method

`run-evals` runner, working tree only, one run per eval, 10 headless executors and 10 graders on Sonnet 5.5 in four parallel iterations. Cost: executors about 5.3M tokens and $4.08, graders about 2.7M tokens and $2.09.

## Results

| Set | Eval | Pass | Failed expectations |
|---|---|---|---|
| audit-run | 2 auditor-finds-planted-defects | 7/8 | 7: seg-1 F3 misread the Agent step's description as the prompt (an auditor false positive) |
| audit-run | 5 audit-writes-ledger | 15/16 | 7: a WARN heading read `— · none` for a finding with no valid fault, not a `TO-nnn` id |
| audit-run | 6 audit-checks-prior-fixes | 14/14 | none |
| run-flow | 1 chart-by-session-id | 6/8 | 1 and 5: executor's `transcript.md` was a summary with no build command; closing line gave segments, not waves |
| run-flow | 2 title-words-and-fork-question | 5/7 | 1 and 3: same, the flags are not in the transcript |
| run-flow | 3 writer-across-two-sessions | 8/8 | none |
| fix-issues | 1, 2 | 11/11, 8/8 | none |
| bump-version | 1, 2 | 8/8, 5/5 | none |

## Verdict

No failure is about a path. The two audit-run misses are the auditor's and the executor's, the four run-flow misses are executors that summarised their transcript, which the set's own expectations and the earlier Opus iteration (`2026-10-07-run-flow-behavioral.md`, 15/15) show is a Sonnet executor effect. One real defect surfaced and was fixed in `32f7d7f`: `fix-issues` §6.5 and `audit-run` §5.7 still said `git add audits`. Left open, as graders' remarks on the expectations: run-flow's expectations that read flags out of `transcript.md`, and audit-run eval 5's W-heading rule for a finding with no valid fault.
