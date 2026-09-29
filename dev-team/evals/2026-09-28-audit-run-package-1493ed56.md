# audit of a real `/dev-team:run-package data` run (quant, session 1493ed56)

**Tested against:** dev-team `1.0.0` (tag `dev-team-v1.0.0`, `3b5bd12`) as installed at `~/.claude/plugins/cache/cott-plugins/dev-team/1.0.0` · model: `claude-opus-5-5` (the run and the auditors) · 2026-09-28
**Set:** none, an audit of a real run with `plugin-dev`'s `audit-run` (uncommitted, branch `audit-run`) · **Baseline:** none

## What was tested

Did a real `run-package data` run on the `quant` repo do what dev-team 1.0.0's own agent and skill files say? This covers the inputs each agent was sent, its procedure, its write scope, whether its claims are backed by its tool calls, how the driver branched on each return, and consistency across agents.

## Method

- **Trace.** `trace.py build` over session `1493ed56` (project `/Users/connorott/PycharmProjects/quant`, branch `data_build`). It found 55 units and 186 driver steps; the run was still in progress, with U55 running.
- **Auditors.** Four units were audited by name: U03 (researcher, edgar), U14 (first implementer), U27 (the reviewer that returned `blocked`) and U43 (an implementer the selector flagged for no commit). The driver segment and a cross pass were audited too. That is 6 auditors, run as `general-purpose` agents following `plugin-dev/agents/run-auditor.md`, because the agent is not installed from the branch.
- **Spot-check.** Every ERROR's cited rule line was read under the 1.0.0 root, and 9 findings' trace evidence was checked against the project's git history.
- **Report.** `evals/workspace/audit/1493ed56/report.md` (gitignored). Auditor cost was about 0.9M subagent tokens.

## Results

Auditors wrote 30 ERROR, 16 WARN and 21 NOTE. Merged, there are 17 errors. None was dropped on spot-check. Every definition fault is still at HEAD `4def96d`.

| Id | Unit | Fault | Finding | Rule |
|---|---|---|---|---|
| E1 | cross, U14, U43 | definition | 9/9 implementers let through after 3 attempts: repo-wide `ruff check` fails on `tests/intent/edgar`, which no role may fix | `hooks/gate_on_stop.py:198`, `agents/tester.md:53-56`, `agents/implementer.md:313` |
| E2 | cross, U14, U43 | definition | Post-gate return never reaches the driver: only the last `SubagentHandback` is delivered, not the last turn | `agents/implementer.md:341-344, 542` |
| E3 | cross | definition | One `gate.txt` per repo; round-1 reviewers of four sections read edgar's gate | `hooks/gate_on_stop.py:406-408` |
| E4 | cross, U27 | definition | Parallel reviewers share `docs/deviations.md`; 2994d5e holds other sections' approvals | `skills/run-package/SKILL.md:132-133, 215-218` |
| E5 | cross | definition | Reviewer B's spec-change has no route to the ledger; it cost a no-op regeneration and review round | `agents/reviewer.md:217-220` |
| E6 | cross, U27 | definition | Design §10 contract deviations never reach the ledger or `sync-plan` | `agents/designer.md:211-216`, `skills/sync-plan/SKILL.md:3` |
| E7 | U03, seg-1 | definition | Researcher return has no `Result:` line; the driver branches only on `Result:` | `agents/researcher.md:201-202` vs `skills/run-package/SKILL.md:219, 226` |
| E8 | seg-1 | definition | Designer Mode resolves to `new` when a spec-change reopens an existing design | `skills/run-package/SKILL.md:100` vs `agents/designer.md:135` |
| E9 | U14 | definition | Lint `D` (D104) contradicts "every nested `__init__.py` is empty" | `pyproject-lint-config.toml:16` vs `skills/project-structure/SKILL.md:77` |
| E10 | U27 | agent | Approved a silent deviation (`client.py:224`) that its retry graded CRITICAL | `agents/reviewer.md:140, 286` |
| E11 | U03 | agent | "Three runs, ~335 GETs each, no 429" not backed by the trace | `agents/researcher.md:35` |
| E12 | U03, U14, U27, U43 | agent | Returns over line caps; Gate field in no allowed form | each agent's Return section |
| E13 | U14 | agent | `mkdocs build` late, `TODO(decision` sweep skipped, plugin root grepped | `agents/implementer.md:206-207, 254, 21` |
| E14 | U43 | agent | Intent suite not run before code; backlog claim unread | `agents/implementer.md:192, 295` |
| E15 | seg-1 | driver | Driver `sed -i`-edited the package contract at D46, uncommitted | `skills/run-package/SKILL.md:25` |
| E16 | seg-1 | driver | git, reads and return-reading outside the driver's allowed lists | `skills/run-package/SKILL.md:26-35` |

The warnings include:
- 52 of 54 commits carry a `Co-Authored-By` trailer against "one trailer and nothing else".
- `status.py` marks round 1 DONE from half a pair, and accepts non-path Sections cells.

## Verdict

The run did not conform. Nine errors are faults in dev-team's own files, all still at HEAD. E1–E4 are systemic: they fire on every multi-section run, not by chance. The fixes are proposed in the report and not made here.
