# run-flow and audit-run phase 1 behavioral rows — not run: Sonnet 5.5 executors refused at their first message

**Tested against:** uncommitted — see working-tree diff on branch `plugin-dev-0.16-audit-ledger` (on `039fddf`): `skills/run-flow/SKILL.md`, `skills/run-flow/scripts/`, `skills/audit-run/SKILL.md` · model: `claude-sonnet-5-5` (executors, via the Agent tool's `sonnet`) · 2026-10-07
**Set:** `evals/sets/run-flow.json` evals 1, 2 (B1.1) · `evals/sets/audit-run.json` eval 2 (B1.2) · **Iteration:** `evals/workspace/run-flow/iteration-1`, `evals/workspace/audit-run/iteration-1` · **Baseline:** B1.1 none (`without_skill`); B1.2 previous, resolved to `359f45e` (`old_skill`) · **Pass rate:** not run — 5 of 6 executor runs ended on an API error twice; nothing graded

## What was tested

Nothing yet. B1.1 is the claim that `run-flow` builds the planted session's chart and unit page
from its id or its title (asking once between the chat and its fork) and judges nothing; B1.2
that `run-auditor` still finds the five planted defects in a trace built by the moved script.

## Method

`run-evals`' behavioral loop: `eval_workspace.py init` for each target, then the six executors
(with and baseline for run-flow 1 and 2, and for audit-run 2) spawned in one message as
general-purpose agents on Sonnet 5.5 with the verbatim executor prompt. For B1.2 the prompt also
spelled out eval 1's build command and that `run-auditor` is the plugin root's
`agents/run-auditor.md`, run by general-purpose proxies (the installed `plugin-dev:run-auditor`
is the 0.15.0 cache, not the plugin root under test).

Five of the six ended within seconds on `API Error: Sonnet 5.5's safeguards flagged this
message … [reasoning_extraction]` before writing anything. Per `run-evals` step 3 each was
rerun once with the same prompt, and each ended on the same error again, so all five are
recorded as not run. The sixth, run-flow eval 2 `without_skill`, finished (75,822 tokens,
84 s); it is not graded, since a baseline alone says nothing about the pass bar.

## Results

| Run | First attempt | Rerun | Result |
|---|---|---|---|
| run-flow 1 · with_skill | safeguard error | safeguard error | not run |
| run-flow 1 · without_skill | safeguard error | safeguard error | not run |
| run-flow 2 · with_skill | safeguard error | safeguard error | not run |
| run-flow 2 · without_skill | finished | — | outputs kept, ungraded |
| audit-run 2 · with_skill | safeguard error | safeguard error | not run |
| audit-run 2 · old_skill | safeguard error | safeguard error | not run |

## Verdict

No verdict: B1.1 and B1.2 are unmet for want of runs, not for a failure. The phase stops before
its commit and asks whether to rerun these rows on another executor model (the note and
`run-evals` name Sonnet 5.5; only the user can name another) or retry Sonnet 5.5 later. A rerun
gets its own iteration and its own log.
