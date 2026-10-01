# audit of a real run-package content run (session befb4798)

**Tested against:** `b82757f` (tag `dev-team-v2.2.0`; `skills/run-package/SKILL.md`, `agents/implementer.md`, `agents/tester.md`, `agents/reviewer.md`, `agents/designer.md`, `agents/architect.md`; HEAD `36cb237` has no `agents/` or `skills/` change since) · model: `claude-opus-5-5` (every audited agent and the driver) · 2026-09-30
**Set:** none — an audit of a real run, not a set eval · **Iteration:** `evals/workspace/audit/befb4798` (gitignored) · **Baseline:** none · **Pass rate:** —

## What was tested

`/dev-team:run-package content` as it ran in `~/PycharmProjects/wild-ones` (branch `design`, 2026-09-30 17:50 → 22:45): did the driver and the agents do what the plugin's files say. Four sections (schemas, data, catalog, surface), 29 units, 127 driver steps. The chat is titled "Plan-package content"; its one segment is `run-package content`, and the `plan-package` architect (`U01`) ran inside it.

## Method

Session `befb4798-1ef6-4b83-afac-f959d36d6d1e`, built into a trace with `audit-run`'s `trace.py`. Units chosen with `--units risk`: 12 of 29 (U02, U03, U04, U06, U09, U11, U12, U16, U19, U23, U24, U29), plus the driver segment and a cross-run auditor, 14 `run-auditor` agents in all. `U01` was not offered by `select` (trace marks it unfinished). Every ERROR was spot-checked against the trace and the cited definition line, U24's `Gate: PASS` against the raw transcript because the trace truncates that step. Rules are at the version that ran, and `agents/` and `skills/` are unchanged since its tag, so each `definition` finding is still at HEAD. The report is `evals/workspace/audit/befb4798/report.md` (gitignored), so the ERROR table is below.

## Results

13 ERROR · 17 WARN · 26 NOTE after merging. None dropped on spot-check.

| Id | Unit | Fault | Finding | Rule |
|---|---|---|---|---|
| E1 | seg-1, U24 | definition + agent | A `Result: blocked` return was not asked about; `status.py` ignores the stop marker, the row went to REVIEW, and the run closed `done` with the surface FAIL still in the repo | `skills/run-package/SKILL.md:261` |
| E2 | cross | definition | *Needed from elsewhere* has no consumer; the S603 hit in `tests/intent/data/test_workflow.py:92` was reported three times and shipped | `agents/implementer.md:671-672` vs `skills/run-package/SKILL.md:247-248` |
| E3 | 9 units | definition | The closed return lists were broken in nine units; the rule sits away from the steps that produce the extra facts | `agents/tester.md:262`, `agents/implementer.md:708-712`, `agents/architect.md:614` |
| E4 | seg-1 | agent | Driver read repo files with `grep … \| head` (`D10`) | `skills/run-package/SKILL.md:34-40` |
| E5 | U06 | agent | Reviewer never read the 125 intent tests | `agents/reviewer.md:173-175` |
| E6 | U06 | agent | Reviewer ran `git ls-files` and `git status --short` in Bash | `agents/reviewer.md:100-105` |
| E7 | U11 | agent | RED paragraph read with `grep`, not Read (four of five testers; W1) | `agents/tester.md:166-167` |
| E8 | U12 | agent | 33 section files written by script and `cp -R` | `agents/implementer.md:29` |
| E9 | U12 | agent | "No stale markers were found" with no `TODO(decision` grep | `agents/implementer.md:354`, `:702` |
| E10 | U24 | agent + definition | First hand-back said `Gate: PASS` over a FAIL the agent had seen | `agents/implementer.md:737`, `:702` |
| E11 | U24 | definition | The blocked amendment cannot go through `SubagentHandback`, which delivers one report | `agents/implementer.md:451`, `:700` |
| E12 | U24 | agent | `mkdocs.yml` and `members` edits beyond the nav entry and the module's names | `agents/implementer.md:568-570` |
| E13 | U29 | agent | Closing architect never read `references/change.md` (definition and skill disagree on which references a close reads) | `skills/sync-plan/SKILL.md:41-42` |

WARN, by theme: the `Gate: PASS` line has no backing before the gate runs (W3); implementers end on prose after the hand-back (W2); `Resolved by:` reads two ways and was set to the reviewed commit (W4); the driver printed prose after every batch and inferred a `Previous round:` name (W5, W6); a tester dodged a lint hit and another dropped a case silently (W10, W14); partial or unbacked claims in U02, U23, U29 (W8, W15–W17).

## Verdict

Not clean: 13 ERROR. Of those, the agent-side faults are E4–E9, E12 and E13, which are one-off lapses against clear rules. The ones that go back to the definition are E1, E2, E3, E10 and E11 (plus the definition half of E8): all still at HEAD. E1 is the one that matters most, because the run reported `done` over a failing surface check and the stop marker that should have caught it is invisible to `status.py`. No edits were made; the report offers them for the user to approve. A fix would need `check-contracts`, `build-site` and a re-run of the evals that cover it. Sixteen of 28 units were not audited, so the systemic counts may be low.
