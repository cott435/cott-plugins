# audit of a real run-package lm run (session 9ecf4176)

**Tested against:** `07dcb19` (tag `dev-team-v2.3.0`; `skills/run-package/SKILL.md`, `agents/implementer.md`, `agents/tester.md`, `skills/status/scripts/status.py`; the working tree's copies are byte-identical to the 2.3.0 cache that ran) · model: `claude-opus-5-5` (every audited agent and the driver) · 2026-10-01
**Set:** none — an audit of a real run, not a set eval · **Iteration:** `evals/workspace/audit/9ecf4176` (gitignored) · **Baseline:** none · **Pass rate:** —

## What was tested

`/dev-team:run-package lm` as it ran in `~/PycharmProjects/slm` (branch `main`, 2026-09-30 22:49 → 10-01 09:17): did the driver and the agents do what the plugin's files say. Scaffold, then tokenizer, arch, prompt and checkpoint, with probe-driven re-designs and four spec-change stops; 35 units, 155 driver steps. The chat is titled "Plan package LM". Run on 2.3.0 (the trace flags 2.2.0 for the `plan-package` architect `U01`, which was still running and never selected).

## Method

Session `9ecf4176-309c-419e-9ecc-573e6a5026cd`, built into a trace with `audit-run`'s `trace.py`. Units chosen with `--units risk`: 12 of 35 (U04, U05, U07, U13, U16, U17, U19, U20, U23, U30, U32, U35), plus the driver segment and a cross-run auditor, 14 `run-auditor` agents in all. No designer, researcher or reviewer unit was selected. Every ERROR was spot-checked against the trace and the cited rule line; U20's per-heading test count was re-derived from the commit, and `status.py:643-649` was read for E1. The report is `evals/workspace/audit/9ecf4176/report.md` (gitignored), so this entry carries the table.

## Results

12 ERROR (31 as filed) · 25 WARN · 41 NOTE after merging. None dropped on spot-check.

| Id | Unit | Fault | Finding | Rule |
|---|---|---|---|---|
| E1 | seg-1, U32, U34, U35 | definition | Two open `spec-change:test` entries from one commit were handed down as one; `answered()` closed both, the section reached REVIEW with a red intent test, and the driver asked the user | `agents/implementer.md:656-657`, `status.py:643-649` |
| E2 | 10 units | agent + definition | The closed return lists were broken in at least 10 of 12 units | `agents/tester.md:266-268`, `agents/implementer.md:733-736` |
| E3 | U07, U19, U32, U35 | definition | `implementer.md` invites a security paragraph in the return and forbids any line outside the list | `agents/implementer.md:357` vs `:733-736` |
| E4 | U13, U23, U35 (+U05, U20, U17) | agent | Upstream `interface.md`, `TODO(decision` sweep and `security-review` Verification steps skipped or only grepped, returns assert the result | `agents/implementer.md:77`, `:363`, `:355-356`, `agents/tester.md:166` |
| E5 | U04, U16, U17, U20, U30 | definition | `tester.md` says `test-driven-development` is preloaded; the frontmatter does not list it, and three testers never read it | `agents/tester.md:7-10` vs `:168-171` |
| E6 | U04, U20, U30 | agent | A project memory note recommends the `test_zz_selfcheck.py` route the Hard rules close; three testers ran it and did not correct it | `agents/tester.md:49-54`, `:332-333` |
| E7 | seg-1 | agent | The driver's Ask relayed a `spec-change` return past its first line (`D134`) | `skills/run-package/SKILL.md:28-33` |
| E8 | seg-1 | agent | Driver read the contract with `grep … \| head` (`D9`); Glob unavailable, no sanctioned existence check | `skills/run-package/SKILL.md:34-40` |
| E9 | seg-1 | agent | Changed rows not printed after seven re-derives; a sentence twice | `skills/run-package/SKILL.md:272-274` |
| E10 | U04 | agent | `ls /opt/anaconda3/...` outside the repo root | `agents/tester.md:55` |
| E11 | U17 (U20) | agent + definition | A passing test deleted in `delta` mode and returned as `Deleted for passing: n/a`; `delta` on a never-built section is undefined | `agents/tester.md:201`, `:282` |
| E12 | U20 | agent | `Tests:` count by design heading wrong (§3 20/19, §5 20/17, §7 27/29, §8 2 missing) | `agents/tester.md:274` |

Warnings worth carrying: integration and e2e tests have no path in the designer or implementer rules and each section files a deviation (`agents/designer.md:229` vs `agents/implementer.md:415`); `lint-imports`/`ruff format` results returned with no output in the trace (U07, U23).

## Verdict

Not clean. Five definition faults (E1, E3, E5, E11 and the unplaced test path) are still at HEAD; E2, E4 and E6 are agent faults that definition edits would help. The audit was a sample (12 of 35 units, no designer, researcher or reviewer), so every repeat count is a lower bound. No definition edits were made.
