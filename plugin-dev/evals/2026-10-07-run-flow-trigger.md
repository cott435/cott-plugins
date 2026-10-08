# run-flow — does its scoped description trigger on run questions in a plugin directory, and only there

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `039fddf`): `skills/run-flow/SKILL.md` `description:` as written in phase 1 · skill-creator `run_eval.py` from `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator` · model: `claude-opus-5-5` · 2026-10-07
**Set:** `evals/sets/run-flow.trigger.json` (19 queries: 9 should, 10 should-not) · **Iteration:** `evals/workspace/run-flow/trigger/` (gitignored) · **Baseline:** none, a new skill · **Trigger rate:** 1.00 → 1.00 (no optimization: at or above 0.9, so `run_loop` was not run and the description is unchanged)

## What was tested

T1.1 of `site/notes/0.16-audit-ledger-01-run-flow.md`, the design's one assumed platform fact: a
model-invocable description scoped "only inside a plugin's own subdirectory … or from the
marketplace repo that holds it" fires when someone asks what a run or an agent did from a
plugin directory, and does not fire on the same question asked from an ordinary project, on an
audit request, or on chat history and logs.

## Method

Real runs, the method in `run-evals` **Trigger evals**: a scratch project in the session
scratchpad with its own `.claude/` and `{"enabledPlugins": {"plugin-dev@cott-plugins": false}}`,
`PYTHONPATH=<skill-creator> python3 -m scripts.run_eval --skill-path plugin-dev/skills/run-flow
--num-workers 1 --runs-per-query 3 --model claude-opus-5-5`, all 19 queries, no holdout. 57
`claude -p` calls, about 20 minutes, in the background.

## Results

| Group | Queries | Triggered | Pass |
|---|---|---|---|
| should-trigger: a run or agent question from a plugin dir or the marketplace root | 9 | 27/27 runs | ✅ 9/9 |
| should-not, scoping: the same question from a flask project, a plain python repo, a react app | 3 | 0/9 | ✅ 3/3 |
| should-not, audit: "did each agent follow its definition", "did the reviewer follow its rules" | 2 | 0/6 | ✅ 2/2 |
| should-not, other: chat history (2), application logs, a code flow chart, a CI run | 5 | 0/15 | ✅ 5/5 |
| **Score** | 19 | | **1.00** |

## Verdict

Held: 1.00, and every scoping query at 0/3. The fact is written back to `plugin-anatomy`
`references/skills.md`, **Descriptions**, as `[proven: evals/2026-10-07-run-flow-trigger.md]`
on the "plugin installed everywhere" bullet. Phases 2 and 8 widen the description and rerun
this set as a regression row.
