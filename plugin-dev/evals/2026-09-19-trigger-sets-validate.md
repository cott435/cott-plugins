# `eval_workspace.py validate` on trigger sets — the five `*.trigger.json` sets pass, and a set short of should-not queries fails

**Tested against:** uncommitted — see working-tree diff (`skills/run-evals/scripts/eval_workspace.py`, `evals/sets/*.trigger.json`, branch `plugin-dev-0.9-evals` at `5fdfdd9`) · no model (mechanical) · 2026-09-19

## What was tested

P2-M1 of `site/notes/0.9-evals-02-trigger-evals.md`: `validate` accepts a file ending
`.trigger.json` in skill-creator's `[{query, should_trigger}]` format, requires at least 8
of each value and at least 3 should-not queries outside a plugin repo, and names the count
when one falls short.

## Method

`python3 skills/run-evals/scripts/eval_workspace.py validate` on the five new sets (and the
two existing behavioral sets, to check the dispatch leaves them alone); then on a copy of
`log-eval.trigger.json` cut to its 10 should-trigger queries and the first 5 should-not
ones, in the session scratchpad. Seconds; no model.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| `{log-eval,build-site,check-contracts,new-plugin,run-evals}.trigger.json` + `plan-phases.json` + `run-phase.json` | exit 0, no output | exit 0, no output; each trigger set is 10 should / 10 should-not | ✅ |
| copy with 5 should-not queries | exit 1 naming the count | exit 1: `neg.trigger.json: 5 should-not-trigger queries; at least 8 needed` | ✅ |

## Verdict

Held. The outside-a-plugin heuristic (query text lacks `plugin`, or says "not a plugin")
counts 5–9 such queries per set; none needed rewriting to reach 3.
