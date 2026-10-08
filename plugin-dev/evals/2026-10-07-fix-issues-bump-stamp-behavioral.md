# fix-issues and bump-version phase 6 — fixes recorded as Fix attempts on a worktree branch (B6.1); a bump stamps fixed_in, and a plugin with no audits/ bumps as before (B6.2)

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `1984aa1`): `skills/fix-issues/SKILL.md` (new), `skills/bump-version/SKILL.md` · model: Sonnet 5.5 (`sonnet`) for executors, graders and comparators · 2026-10-07
**Set:** `evals/sets/fix-issues.json` evals 1, 2 (B6.1); `evals/sets/bump-version.json` evals 1, 2 (B6.2) · **Iteration:** `evals/workspace/fix-issues/iteration-1`, `evals/workspace/bump-version/iteration-1` · **Baseline:** B6.1 none (`without_skill`); B6.2 previous = `359f45e` (`old_skill`) · **Pass rate:** B6.1 with_skill 19/19 (100%) vs without_skill 11/19 (58%); B6.2 with_skill 13/13 (100%) vs old_skill 9/13 (69%) · **Blind:** B6.2 new preferred 2/2

## What was tested

B6.1: that `/plugin-dev:fix-issues` selects open (or named recurred) issues, gets one approval
of a one-edit-per-issue plan before any edit, edits on a `<P>-audit-fixes-<date>` worktree
branch in two commits (edits, then attempts), records each Fix attempt through `issues.py` with
a Verify line naming what a trace shows, leaves the ledger clean and nothing verified, and
merges and bumps nothing without a yes. B6.2: that `bump-version` on a plugin with `audits/`
runs `issues.py stamp` and stages the stamped ledger with the bump, which the 0.15 skill does
not, and that a plugin with no `audits/` bumps exactly as before.

## Method

- One run per configuration, all eight executors in one message on Sonnet 5.5, then one
  skill-creator grader per run, `aggregate_benchmark`, and for B6.2 (an `old_skill`
  baseline) skill-creator's comparator per eval.
- Every fixture is built from `evals/fixtures/audit-run/make_session.py` in a `mktemp -d`
  directory under the session scratchpad; branches, worktrees and commits happened only there.
- **Rerun:** fix-issues eval 2 `with_skill` ended on an API error (Sonnet 5.5 safeguard,
  `reasoning_extraction`) after writing part of its outputs; its outputs were emptied and it
  was rerun once with the same prompt, which finished. Nothing was recorded as not run.
- **Harness note:** the B6.2 baseline snapshot has no `evals/`, so its seed's
  `$PD/evals/fixtures/audit-run/make_session.py` does not exist there. All four B6.2 prompts
  carried one added sentence pointing the seed at the working tree's copy of that script
  (the fixture, not the target).
- The grader prompts named each eval's expectations by a file staged in the session scratchpad
  (outside the iteration), written after every executor had finished.
- **Expectations corrected (run-evals step 7)**, from the graders' critiques:
  - fix-issues eval 2 expectation 1 named only `transcript.md` or `final-message.md` for the
    one-row selection table; the with_skill run put it in `outputs/interview.md` (the shown
    plan and question), and its grader failed it "on where the table lives, not on what the
    run did". It now also accepts `outputs/interview.md`. Both eval 2 runs were regraded on the
    corrected set: with_skill 7/8 → 8/8; without_skill stays 6/8 (it shows no table anywhere).
  - fix-issues evals 1 and 2, "no `issues.py check-result` call": scoped to after the fixture
    setup, since eval 2's own seed makes one. No verdict changed.
  - bump-version evals 1 and 2, "no git other than reads before the yes" and "no `git commit`,
    `git tag` or `git push` anywhere": scoped to after the seed, which runs `git init`,
    `commit` and `tag` itself. No verdict changed (graders had read them that way).
  - The three harness files (`fix-issues/fixture.md`, `bump-version/with-audits.md`,
    `no-audits.md`) gain a section requiring every shell command verbatim in
    `transcript.md`: every grader noted the transcripts were prose summaries, so ordering
    expectations rested on step numbers. Not rerun: no verdict depends on it.
- Cost: about 0.60M executor tokens (including the errored run's) and 0.85M grader and
  comparator tokens.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| B6.1 eval 1 with_skill | 11/11 | 11/11: one `AskUserQuestion` (Approve the plan / Change it) before any edit; TO-001 edited at ship step 2 (an unexpected first line prints `unexpected writer return:` and stops); TO-002 `wontfix` with a reason; commits `7cac65b` (edits) then `c1443b5` (attempts) on `toy-audit-fixes-20261007`; Verify `watch driver:ship; held when …; recurred when …`; `ok: 2 issues`; no merge, no bump, "minor … waits for your yes" | ✅ |
| B6.1 eval 1 without_skill | fails ≥1 | 5/11: no AskUserQuestion, branch `toy_fix-open-issues`, Verify without `watch driver:ship;`, no checks step, no bump level | ✅ (bar) |
| B6.1 eval 2 with_skill (rerun) | 8/8 | 7/8 on the set as written (the table was in `interview.md`); 8/8 on the corrected expectation: attempt 2 on `agents/writer.md` added by `issues.py fix`, attempt 1 and its `recurred` Checks line untouched, `5384731` on `toy-audit-fixes-20261007`, INDEX `fixed`, `ok: 3 issues` | ✅ after correction |
| B6.1 eval 2 without_skill | fails ≥1 | 6/8: no selection table, a two-edit plan that does not say why the issue is back | ✅ (bar) |
| B6.2 eval 1 with_skill | 8/8 | 8/8: `issues.py stamp --version 0.2.0` after the yes; TO-001 `fixed_in: 0.2.0`, INDEX `released` / `0.2.0`; TO-002 untouched and `open`; five paths staged in one commit; tag `toy-v0.2.0`; nothing committed, tagged or pushed | ✅ |
| B6.2 eval 1 old_skill | fails ≥1 | 4/8: no stamp, no TO-001 `fixed_in`, no INDEX, three paths staged | ✅ (bar) |
| B6.2 eval 2 with_skill | 5/5 | 5/5: same three-file bump, no `issues.py`, no `audits/` | ✅ |
| B6.2 eval 2 old_skill | 5/5 (passes on both) | 5/5 | ✅ |
| B6.2 blind | — | eval 1: with_skill 10 vs 7 (only it stamped the ledger); eval 2: with_skill 10 vs 9 (old proposal miscounted the commits) | new 2/2 |

## Verdict

Held. B6.1: every expectation passes for `with_skill` (eval 2 after one location-only
expectation correction, regraded), and `without_skill` fails at least one per eval. B6.2: every
expectation passes for `with_skill`; eval 1 fails four for `old_skill`; eval 2 passes on both,
so a plugin with no `audits/` bumps exactly as before. Observed in both fix-issues `with_skill`
runs: the attempts commit (§6 step 5, `git add audits`) was first run from the worktree root
rather than `<worktree>/<P>/` and failed once before the executor reran it from the plugin
directory.

**After review:** the reviewer approved the eval 2 expectation correction and asked for the
path fix: §6 step 5 now says to commit the attempts from `<path>/<P>/`, not the worktree's
root. A wording change to where a command runs; not rerun.
