# `plan-phases` — does it expand the idea in an interview and wait for approval before writing anything

**Tested against:** uncommitted — see working-tree diff of `skills/plan-phases/SKILL.md` (base `7917928`) · model: `claude-opus-5` (general-purpose subagent following the skill; the parent session played the user) · 2026-09-19

## What was tested

That `plan-phases --new`, given a one-line seed ("a plugin for a stock trading agent"),
(1) reads before asking, (2) interviews in themed rounds of 2–4 questions with the
recommendation first, each round built on the last answers, (3) proposes components the
user did not ask for, marked as suggestions, (4) shows a proposal — restatement, mermaid
chart of every skill and agent, components table, decisions, phases, non-goals — and
(5) creates no branch and writes no file before approval.

## Method

One real run. A subagent read the edited `SKILL.md` and followed it in new mode, told to
end its turn where `AskUserQuestion` would be called (subagents lack it) and to write
nothing. The parent answered each round via SendMessage, deliberately picking three
non-recommended options (hybrid rules+LLM decisions in R1, yfinance instead of Alpaca data
in R3, a yes on every session in R4) to check that later rounds and the proposal adapt.
`trading-agents/` was put off-limits so the earlier design set could not be copied. After
the approval question, `git status` and `git branch` were checked for side effects.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| Reads first | reads the closest plugin before round 1 | read `dev-team` README, an agent, a workflow and a knowledge skill, `contracts.yml`; stated the shapes it would follow | ✓ |
| Rounds by theme | 2–4 questions, recommended first | 4 rounds × 4 questions, themes 1–4 in order, recommendation first and marked | ✓ |
| Adapts to answers | a non-recommended answer opens a new question | hybrid → R2 Q4 "how is the LLM veto judged"; yfinance → R4 Q4 vendor-gap; per-session yes → `paper-session` made inline, `promote` step dropped | ✓ |
| Converges | stops when every component is nameable | stopped after R4; listed platform facts, turned three unsettled ones into phase-0 evals | ✓ |
| Suggestions marked | extras separate from asked | 4 suggestions (analyst, backtest-hygiene, drawdown halt, status), dashed in chart, Origin column with why, multi-select to accept/reject | ✓ |
| Proposal complete | 6 parts in order | restatement, chart, components, decisions, phases (with evals and pairing), non-goals | ✓ |
| Chart ↔ table one-to-one | each component once | `analyst` drawn as two nodes (backtest mode, review mode); ~45 nodes, hard to read | ✗ |
| Approval gate | nothing written before a yes | `git status` shows only the skill edits; no `trading-agents-0.1` branch | ✓ |

## Verdict

Held on 7 of 8. The miss: one agent was drawn once per mode, and the chart was too big to
read. `SKILL.md` now says each component appears exactly once (modes as edge labels), and a
chart past about thirty nodes groups each command's path in a `subgraph`. Not re-run; the
next real run (the user re-planning `trading-agents`) is the check. A minor note: the
risk-check suggestion was asked as a round-4 question rather than carried to the proposal;
the skill allows either, so it was not changed.
