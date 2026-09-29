# audit · run-package data · quant session f1c390a1

**Tested against:** `c34a755` (tag `dev-team-v2.0.0`, as installed at `~/.claude/plugins/cache/cott-plugins/dev-team/2.0.0`) · model: `claude-opus-5-5` · 2026-09-29
**Set:** none, an audit of a real run · **Baseline:** the 1.0.0 audits `2026-09-28-audit-run-package-1493ed56.md` and `2026-09-29-audit-run-package-5976c083.md`

## What was tested

This checks whether a real `/dev-team:run-package data` on quant (restarted on `data_build`, two segments) conforms to 2.0.0's own agent and skill files. It is the first run on 2.0.0, so it also checks whether the audit fixes 1–9 behave as intended.

## Method

- **Session:** `f1c390a1`, project `/Users/connorott/PycharmProjects/quant`, 14:27–17:30. 29 units; U29 (the data/digest tester) was still running when the trace was built.
- **Tooling:** the trace was built with `plugin-dev:audit-run` (trace.py from 0.12.1).
- **Selection:** `--units risk` picked 12 units: U01, U02, U03, U04, U12, U15, U16, U17, U18, U19, U20, U22. Each got a `run-auditor` in `unit` mode, and both driver segments got one in `driver` mode. That is 14 auditors in parallel, then one `cross`.
- **Spot-check:** I checked every ERROR class against the trace, the quant repo and the 2.0.0 files. None was dropped.
- **Report:** `dev-team/evals/workspace/audit/f1c390a1/report.md` (gitignored). The findings are carried below.
- **Cost:** no workflow was re-run. The 15 auditors used about 1.35M subagent tokens.

## Results

The auditors filed 48 ERROR, 26 WARN and 62 NOTE. After merging systemic findings: 18 ERROR and 17 WARN.

| ID | Unit(s) | Fault | Finding | Rule | At HEAD |
|---|---|---|---|---|---|
| E1 | U03, U05, U07, U09 (cross F1) | definition | Parallel `a` reviewers split on designer §10 contract-row deviations: priceaudit's were rejected, the others' approved. This caused priceaudit's PLAN detour and contradictory reviewer memory. | `reviewer.md:295-297` vs `designer.md:222-229` | yes |
| E2 | 9 units (cross F2) | definition | Returns add undefined fields and run past their line caps; the content is lost to the driver. | `tester.md:209-229`, `implementer.md:612`, `reviewer.md:370` | yes |
| E3 | U12, U15, U16, U18, U19, U20, U22 (cross F3) | definition | Delta and fix runs skip the contract, repo contract, decisions, READMEs and the TDD RED paragraph. | `implementer.md:56`, `tester.md:132-133,171`, `designer.md:146-168` | yes |
| E4 | U01, U12, U15, U19, U22 (cross F4) | definition | Repo files are written through Bash, so the ruff hook and write guard (`Write\|Edit` only) never run. | `hooks/hooks.json:6,22` | yes |
| E5 | U04, U16, U18, U20, U22 (cross F5) | definition | Shell commands name harness tool-results and scratchpad paths outside the repo. | `implementer.md:19`, `reviewer.md:102`, `tester.md:49` | yes |
| E6 | U15, U16, U18 (cross F6) | definition | Testers run code with `python -c`, including the section under test, following a memory note. | `tester.md:32,45-48` | yes |
| E7 | seg-1, seg-2 | driver | The driver relays return bodies to the user. | `run-package/SKILL.md:28,215-217` | — |
| E8 | seg-1, seg-2 | driver | Re-derive greps the status table and narrates instead of printing the changed rows. | `run-package/SKILL.md:246` | — |
| E9 | U15 | agent | No `design-gap` for an Interfaces row with no signature. | `tester.md:114-119` | — |
| E10 | U19, U22 | agent | The design's Skills used were never invoked. | `implementer.md:233` | — |
| E11 | U19 | agent | Bugs were fixed before a failing test (Prove-It). | `implementer.md:297` | — |
| E12 | U04, U12, U16, U19, U20 | agent | False or unbacked claims: 8 vs 9 warnings; "OQ-1–11 unchanged"; 5 vs 6 tags; a memory claim; "no D<n> binds". | return rules | — |
| E13 | U02, U03 | agent | U02's `git show --stat` exposed source file names; U03 used Bash for reads; U03 read the template via `cat`, after the ledger. | `tester.md:32`, `reviewer.md:97,291` | — |
| W1 | U16, U22, U25 (cross F7) | definition | A known `may_snap` design defect shipped DONE, because no role has a way to route a non-gap design defect. | `tester.md:208` | yes |
| W2 | cross F8 | definition | No owner for resolving `spec-change:design\|test`; entries are still open on DONE sections. | `deviations-entry.md:26` | yes |
| W3 | cross F9 | definition | Deviation tags churn; the clause match is too loose. | `tester.md:192` | yes |
| W4 | cross F10 | definition | `Mode: delta` with `Adopted code: no` is undefined for testers. | `tester.md:152-154` | yes |
| W5–W17 | various | agent | Thin security checks, test and lint claims, memory rewritten by shell, scope creep, counts, whole-directory commits, a PLR0913 dodge, driver summary shape. | see report | — |

**Fixes from 2.0.0 seen working:**
- fix 3: per-section gate files;
- fix 4: per-section ledgers, and parallel commits held only their own files;
- fix 5: the `b` report re-opened DESIGN (`open docs/reviews/…-ingest-r1-b.md — spec-change:design`);
- fix 8: delta designers.

**Not exercised:**
- No stop gate exited 2, so there was no gate-retry handback.
- Every gate record shows the package-wide pytest runs as `TIMEOUT`, and `mkdocs` as not run, so fix 1's ELSEWHERE never fired.

## Verdict

The run does not conform: 18 errors. Fixes 3, 4, 5 and 8 behaved as intended. Fix 6 shipped a contradiction (E1): designer.md sends §10 contract deviations to the `a` reviewer, but reviewer.md still rejects anything whose Clause is a contract row. The definition faults E1–E6 and W1–W4 are all still at HEAD (2.1.0). Nothing has been changed in response yet.
