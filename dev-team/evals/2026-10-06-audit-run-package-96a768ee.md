# Audit of a real run-package run — data package, quant-rebuild

**Tested against:** `8d4e8aa` (tag `dev-team-v2.8.0`; `agents/{designer,tester,implementer,researcher}.md` and `skills/run-package/SKILL.md`, `agents/profiler.md` are byte-identical at HEAD) · model: `claude-opus-5-5` (run), `claude-sonnet-5-5` (auditors) · 2026-10-06
**Set:** none — audit of a real run, not a set eval · **Baseline:** none

## What was tested

Whether the real `/dev-team:run-package data` run (session `96a768ee`, `~/PycharmProjects/quant-rebuild`, branch `data_rebuild`, 76 agents, 19 sections of which 8 DONE) followed the agent and skill definitions that governed it.

## Method

`trace.py build` rebuilt the run from its transcripts. `trace.py select --units risk` picked 12 of 76 units (capped); one `run-auditor` each, plus one for the driver segment and one `cross` auditor: 14 in all. On 2026-10-07 the four profiler units (U64, U70, U73, U76) were added on request, for 18 auditors over 16 units. The cross auditor ran before the profilers were added. Every ERROR was spot-checked against the trace step and rule line. Report: `evals/workspace/audit/96a768ee/report.md` (gitignored), so the table below carries the findings. Units not audited: 60, including every reviewer and architect.

## Results

| ID | Unit | Fault | Finding | Rule |
|---|---|---|---|---|
| E1 | U03 U09 U15 U18 U19 U23 U24 U53 U64 U76 | agent | closed-list returns decorated (parentheses, clauses, 13-line researcher return vs 10) | `implementer.md:893`, `tester.md:309`, `designer.md:394`, `researcher.md:39` |
| E2 | U09 U18 U19 | agent | tester ran unscoped `git status --short` | `tester.md:35-36` |
| E3 | U23 U53 U24 | agent | implementer skipped the `TODO(decision` grep and the pre-code intent run; two returns claim marker results no tool call backs | `implementer.md:324,412,541-543` |
| E4 | U23/U24 | agent | parallel units: `pyproject.toml` and `uv.lock` for storage landed in calendars' commit `7c9e2a7`; U24 did not report it | none (cross-unit) |
| E5 | seg-1 | agent | granted "one more round" for data/audit never run; no reviewer spawned | `SKILL.md:270-272,289,423` |
| E6 | seg-1 | agent | Summary says "user asked to stop"; trace has no such request | `SKILL.md:475,451-454` |
| E7 | U05 | agent | rewrote the memory index with Write; wrote a test tree before a defect stop | `tester.md:375,185` |
| E8 | U70 | agent | verify return claims all 18 surviving kinds judged on seeded samples; only 2 checks sampled, K18/K19 never looked at | `profiler.md:137,50` |
| E9 | U70 | agent | "Nothing else was written" after a memory note holding counts and column names | `profiler.md:142,207` |
| E10 | U73 | agent | Bash `cp` of store files to the scratchpad | `profiler.md:43` |

17 WARN and 44 NOTE are in the report. The definition-side NOTEs (no `Not written:` form for a decision binding this section, no README form after a spec-change stop, line-length limits not near the build step, no record of a granted round beyond the driver's memory; for the profiler: memory left out of the write list while `memory: project` invites it, no return form near either mode's last step, `unverified` rows counted as Unexplained by the template but not by verify step 4, no rule for a population the unbuilt section would produce) are all still at HEAD.

## Verdict

10 ERROR (all fault `agent`, none `definition`), 17 WARN, 44 NOTE after merging the systemic findings. No ERROR was dropped on spot-check. Every rule cited is unchanged at HEAD. No edits made; the definition-side gaps behind E1, E3 and E5 are the candidates for a fix, to be followed by `check-contracts`, `build-site` and a re-run of the covering evals.
