# run-flow — does the description, widened for --explain, still trigger in a plugin directory and only there

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `dd6af0f`): `skills/run-flow/SKILL.md` `description:` as widened in phase 8 · skill-creator `run_eval.py` from `~/.claude/plugins/marketplaces/claude-plugins-official/plugins/skill-creator/skills/skill-creator` · model: `claude-opus-5-5` (the session model, per `run-evals` **Trigger evals**) · 2026-10-07
**Set:** `evals/sets/run-flow.trigger.json` (23 queries: 13 should, 10 should-not; 2 should-trigger queries added this phase) · **Iteration:** `evals/workspace/run-flow/trigger-3/` (gitignored) · **Baseline:** phase 2's run, `2026-10-07-run-flow-agent-view-trigger.md` (1.00) · **Trigger rate:** 1.00 → 1.00 (no optimization: at or above 0.9, so `run_loop` was not run and the description is as written)

## What was tested

T8.1 of `site/notes/0.16-audit-ledger-08-run-narrator.md`. The description gained a sentence
about `--explain` and two trigger phrases ("explain what each agent did in that run", "walk me
through what the implementer did in chat 5976c083"). This tests that it fires on the new
explanation requests asked from a plugin directory, and, as a regression check, that it still
does not fire on the same questions from an ordinary project, on an audit request, or on chat
history and logs.

## Method

Real runs, as in phases 1 and 2:

- the scratch project in the session scratchpad, with its own `.claude/` and
  `{"enabledPlugins": {"plugin-dev@cott-plugins": false}}`;
- `PYTHONPATH=<skill-creator> python3 -m scripts.run_eval --skill-path plugin-dev/skills/run-flow
  --num-workers 1 --runs-per-query 3 --model claude-opus-5-5`;
- all 23 queries, no holdout: 69 `claude -p` calls, run in the background.

## Results

| Group | Queries | Triggered | Pass |
|---|---|---|---|
| should-trigger, phases 1 and 2: a run or agent question from a plugin dir or the marketplace root | 11 | 33/33 runs | ✅ 11/11 |
| should-trigger, new: "explain what each agent did in yesterday's run-package chat, in plain English", "walk me through what the implementer did in chat 5976c083, step by step" | 2 | 6/6 | ✅ 2/2 |
| should-not, scoping: the same question from a flask project, a plain python repo, a react app | 3 | 0/9 | ✅ 3/3 |
| should-not, audit: "did each agent follow its definition", "did the reviewer follow its rules" | 2 | 0/6 | ✅ 2/2 |
| should-not, other: chat history (2), application logs, a code flow chart, a CI run | 5 | 0/15 | ✅ 5/5 |
| **Score** | 23 | | **1.00** |

## Verdict

Held: 1.00, with every scoping query at 0/3 (the note's bar: ≥ 0.9, scoping 0/3). The
`--explain` sentence did not make the description fire outside a plugin directory. The
description is now 1,462 characters, under the listing's 1,536 for `description` and
`when_to_use` combined (`plugin-anatomy` `references/skills.md`), with little room left for
another clause.
