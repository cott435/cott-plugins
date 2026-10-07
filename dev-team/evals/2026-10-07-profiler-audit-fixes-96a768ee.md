# Profiler fixes from the 96a768ee audit — return forms, verify honesty, memory, Unexplained

**Tested against:** uncommitted — see working-tree diff of `agents/profiler.md`, `skills/planning-templates/references/data-profile.md`, `skills/git-workflow-and-versioning/SKILL.md`, `evals/sets/profiler.json` on branch `dev-team-2.8-audit-fixes` (base `d381bac`) · model: `claude-sonnet-5-5` (executors, graders, comparators) · 2026-10-07
**Set:** `evals/sets/profiler.json` evals 1–7 · **Iteration:** `evals/workspace/profiler/iteration-1` · **Baseline:** `dev-team-v2.8.0` (`d381bac`) · **Pass rate:** 100% (55/55) vs 98.2% (54/55) · **Blind:** new preferred 4/7

## What was tested

The `profiler.md` edits made for the audit of session 96a768ee (`2026-10-06-audit-run-package-96a768ee.md`, E1 for U64/U76, E8–E10 and the profiler definition notes):
- each mode gets a fixed return form, and verify returns a per-kind `Judged:` line;
- a verify run may not claim kinds it never drew, and may not promise that the kinds which held will be marked verified;
- memory is the one write-list exception and is never staged;
- no `cp`/`mv`/`mkdir` in Bash;
- revise runs redo step 1;
- **Unexplained** counts only twice-rejected kinds;
- personal data goes in **Observed schema**;
- a stand-in population is named under **Provenance**.

## Method

Real subagent runs: 7 evals × 2 configurations, 1 run each, Sonnet 5.5, built by `build.py case-<id>` in a mktemp copy per run.
- **Executor prompt:** the standard text, delivered as a scratchpad file the executor read first. So `profiler.md` was its second Read, not its first.
- **Grading:** 14 graders, then `aggregate_benchmark`, then 7 blind comparators. The comparators see `outputs/` only.
- **The set changed alongside `profiler.md`:**
  - Eval 1's Unexplained expectation now requires the in-no-kind count, since the template no longer counts `unverified` kinds there.
  - A return-form expectation was added to each eval, after this iteration ran. It was not graded here; the table below checks it by hand from each run's final message.
- Nothing was rerun or recorded as not run.

## Results

| Eval | with_skill | old_skill | Return form (hand-checked, new expectation) |
|---|---|---|---|
| 1 profile r0 | 13/13 | 12/13 — Unexplained headline "16 of 16" (the 2.8.0 template's rule) | with: 8-line form ✓ · old: free prose ✗ |
| 2 verify r0 rejects | 8/8 | 8/8 | with: `Judged: K1 6/20, K2 4/20, K3 20/20, K4 1/20` + one `Rejected:` ✓ · old ✗ |
| 3 verify r0 stubs | 9/9 | 9/9 | with: form kept but wrote `Rejected: none` instead of omitting the line ✗ · old ✗ |
| 4 profile r1 new kind | 10/10 | 10/10 | with ✓ · old ✗ |
| 5 profile r1 clean | 8/8 | 8/8 | with ✓ (round line given in full) · old ✗ |
| 6 verify r1 ledger | 8/8 | 8/8 | with: `Judged: K4 1/20` ✓ · old ✗ |
| 7 defer | 7/7 | 7/7 | with: `Deferred: K5, K6` ✓ · old ✗ |

Blind comparison: the working tree was preferred on evals 1, 4, 6 and 7, and the baseline on 2, 3 and 5.
- **Eval 1:** the baseline's Unexplained section contradicted itself.
- **Eval 4:** the baseline's "1 of 16" read as one unexplained row.
- **Eval 2:** won by the baseline on a commit-message trailer alone; the outputs were identical in substance.
- **Evals 3 and 5:** won by the baseline on richer stub and round-1 prose, with every expectation passing on both sides.

## Verdict

The claim holds. All 7 working-tree runs used the new return forms where every baseline return was a free paragraph, and the verify runs' `Judged:` lines make the E8 failure (claiming kinds never drawn) visible. The Unexplained fix shows in evals 1 and 4. No regression in any assertion.

One gap remains: eval 3's `Rejected: none`. The verify **Return** says "none when nothing was rejected", which a run read as a line saying none. It was reworded after this iteration ("leave the line out (never `Rejected: none`)"), and is not yet re-run; the next iteration should grade the new return expectations.
