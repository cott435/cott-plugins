# run-flow — does the description, widened for --agent, still trigger in a plugin directory and only there

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `86c7637`): `skills/run-flow/SKILL.md` `description:` as widened in phase 2 · skill-creator `run_eval.py` from `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator` · model: `claude-opus-5-5` (the session model, per `run-evals` **Trigger evals**) · 2026-10-07
**Set:** `evals/sets/run-flow.trigger.json` (21 queries: 11 should, 10 should-not; 2 should-trigger queries added this phase) · **Iteration:** `evals/workspace/run-flow/trigger-2/` (gitignored) · **Baseline:** phase 1's run of the narrower description, `2026-10-07-run-flow-trigger.md` (1.00) · **Trigger rate:** 1.00 → 1.00 (no optimization: at or above 0.9, so `run_loop` was not run and the description is as written)

## What was tested

T2.1 of `site/notes/0.16-audit-ledger-02-agent-view.md`. The description gained a sentence
about `--agent`, `--sessions` and `--branch` and two trigger phrases. This tests that it fires
on the new agent-view questions asked from a plugin directory. It is also a regression check:
it must still not fire on the same questions asked from an ordinary project, on an audit
request, or on chat history and logs.

## Method

Real runs, as in phase 1:

- a scratch project in the session scratchpad, with its own `.claude/` and
  `{"enabledPlugins": {"plugin-dev@cott-plugins": false}}`;
- `PYTHONPATH=<skill-creator> python3 -m scripts.run_eval --skill-path plugin-dev/skills/run-flow
  --num-workers 1 --runs-per-query 3 --model claude-opus-5-5`;
- all 21 queries, no holdout: 63 `claude -p` calls, run in the background.

## Results

| Group | Queries | Triggered | Pass |
|---|---|---|---|
| should-trigger, phase 1's: a run or agent question from a plugin dir or the marketplace root | 9 | 27/27 runs | ✅ 9/9 |
| should-trigger, new: "list every reviewer run on the data_rebuild branch", "how many times did the profiler run in ca48b249, and what did each do?" | 2 | 6/6 | ✅ 2/2 |
| should-not, scoping: the same question from a flask project, a plain python repo, a react app | 3 | 0/9 | ✅ 3/3 |
| should-not, audit: "did each agent follow its definition", "did the reviewer follow its rules" | 2 | 0/6 | ✅ 2/2 |
| should-not, other: chat history (2), application logs, a code flow chart, a CI run | 5 | 0/15 | ✅ 5/5 |
| **Score** | 21 | | **1.00** |

## Verdict

Held: 1.00, with every scoping query at 0/3. Widening the description for the agent view did
not make it fire outside a plugin directory. Phase 8 widens it again for `--explain` and reruns
this set.
