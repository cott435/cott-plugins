# `run-phase` runs a note's evals through `run-evals`, stops for review, and still runs old-format notes

**Tested against:** uncommitted — see working-tree diff (`skills/run-phase/SKILL.md`, `skills/log-eval/SKILL.md`, `templates/phases/progress.md`, `evals/fixtures/toy-plugin/`); baseline `bab28b8` (0.8.0 `run-phase`) · model: `claude-opus-5` (executors and graders; one nested `without_skill` run of the toy's own eval fell back to Sonnet after two refusals, see Method) · 2026-09-19
**Set:** `evals/sets/run-phase.json` evals 1, 2 · **Iteration:** `evals/workspace/run-phase/iteration-1` · **Baseline:** `bab28b8` (previous) · **Pass rate:** 100% vs 100%

## What was tested

Phase 4 of 0.9-evals (note `site/notes/0.9-evals-04-run-phase-evals.md`):

- **P4-M1** (mechanical): the fixture's set validates and its 01 note has `## Evals` before
  `## Done when`.
- **P4-B1**: on the toy plugin's phase with an `## Evals` table, `run-phase` runs
  `run-evals`, stops for review before committing, commits once and fills the ledger — and
  0.8.0's `run-phase` fails the review-gate expectation.
- **P4-B2**: on the same phase with `## Evals` deleted (a pre-0.9 note), `run-phase` still
  runs the eval its Steps name, logs it and commits once.

## Method

P4-M1: `eval_workspace.py validate evals/fixtures/toy-plugin/evals/sets/farewell.json`, and
the note's `##` headings listed with `awk`.

P4-B1/B2 through `run-evals`: `init . run-phase --evals 1,2` (baseline `previous` →
`bab28b8`), four executors in one message (general-purpose subagents, the verbatim executor
prompt plus: the temp-copy path in the session scratchpad, `${CLAUDE_PLUGIN_ROOT}` mapped to
the worktree's `plugin-dev/` for both configurations so only `run-phase` differed, and "no
browser: use the static viewer"). Each executor ran `run-phase` in a `git init`-ed copy of
the fixture per the harness sheet, and nested its own `run-evals` executors and graders for
`farewell` (E0.5). Four graders with skill-creator's `grader.md`, allowed read-only git in
the temp copies. `finalize`, `aggregate_benchmark`, static viewer. One run per
configuration. Cost: executors 369k tokens, graders 263k.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| P4-M1 validate | exit 0 | exit 0 | ✅ |
| P4-M1 headings | `## Evals` before `## Done when` | line 41 vs line 48 | ✅ |
| P4-B1 `with_skill` | 7/7 | 7/7 — `run-evals` iteration dir created; `interview.md` review stop after the static viewer; one commit `toy 0.2 (phase 1): farewell` with skill, two logs, ledger; no tag, no remote; no `evals/workspace/` | ✅ |
| P4-B1 `old_skill` | fails the review-gate expectation | **7/7 — it stopped for review too** | ❌ |
| P4-B2 `with_skill` | 5/5 | 5/5 — ran the Steps' eval, ledger Notes says "old-format note", one commit | ✅ |
| P4-B2 `old_skill` | (no bar) | 5/5 — ran the Steps' eval, wrote a `## Deviations` entry for the missing table | — |

Why the baseline stopped: its transcript cites the toy ledger's Standing facts ("behavioral
rows stop for review" — the 0.9 `progress.md` template wording, which the fixture uses) and
then `run-evals`' own **Review** stop. The gate reaches 0.8.0's `run-phase` through
`run-evals` (phase 1) and the plan's own files; the discriminating half of P4-B1 cannot fail
with a fixture written in the 0.9 format.

Grader critique of the set (not applied — `run-phase.json` is unchanged in this phase):

- "Nothing was pushed" cannot fail: the temp copy has no remote. A local bare remote in the
  harness setup would make it real.
- The review-before-commit order is self-reported by `interview.md`; nothing independent
  (a timestamp against the commit) checks it.
- Eval 2 does not check that the old-format note is *recorded* (ledger "old-format note" or
  a Deviation) — the behavior the eval exists for.
- Eval 2's expectation 1 accepts any log; it could require the log to name `farewell.json`
  eval 1.
- The toy's own `without_skill` baseline reads `0.2-01-farewell.md`, which quotes the skill
  verbatim, so `farewell`'s benchmark is contaminated (0.8.0 run: 100% vs 100%).
- `aggregate_benchmark` prints "3 runs each" and `<model-name>` for one run per config.

Also observed: the eval-2 `old_skill` executor briefly wrote a stray file `x` in the repo
root and deleted it (`git status` clean afterwards, checked).

## Verdict

P4-M1 held. P4-B2 held. P4-B1 **half held**: the new `run-phase` passes 7/7, but so does
0.8.0 — the review gate is already delivered by `run-evals` plus a 0.9-format plan, so the
bar's "`old_skill` fails the review-gate expectation" is missed. Outcome and the user's
decision are recorded in note 04's `## Deviations`.
