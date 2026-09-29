# Audit of a real `/dev-team:run-package data` run (quant, session 5976c083)

**Tested against:** dev-team 1.0.0, tag `dev-team-v1.0.0` (`9bb17e5`), as installed · model: `claude-opus-5-5` · 2026-09-29
**Set:** none — audit of a real run · **Pass rate:** n/a

## What was tested

`/dev-team:run-package data` resumed on the quant `data_build` branch: implementers for retrieval (U01, U03), priceaudit (U04) and financialaudit (U05), a tester regenerate (U02), and the driver's two segments. This is an audit with `plugin-dev:audit-run`, not a set eval.

## Method

Session 5976c083-2a42-4a6a-815c-bb773869bd41, project `/Users/connorott/PycharmProjects/quant`. Selection `risk`: U01, U02, U04, U05 (U03 unselected, used only via cross). Five auditors (four units, seg-2) plus one cross pass. Rules were checked against the installed 1.0.0 files. Report at `evals/workspace/audit/5976c083/report.md` (gitignored), so the findings are below.

## Results

| Id | Unit | Fault | Finding | Rule |
|---|---|---|---|---|
| E1 | U04, U05, U03 | agent | `Gate:` line wrong or off-list after a failing gate (`PASS` with three FAILs; "not yet known") | implementer.md:550 (1.0.0) |
| E2 | U04 | agent | post-gate finishes are short prose, not the full return | implementer.md:342, :542 |
| E3 | U04 | agent | "48 passed" and the 277 s / 16 s figures match no run | implementer.md:545 |
| E4 | U01 (+U03/04/05) | agent | "no stale markers" with no `grep -rn 'TODO(decision'` | implementer.md:254 |
| E5 | U05 | agent | throwaway tests written into `tests/intent/financialaudit/` | implementer.md:296, :349 |
| E6 | U02 | agent | regenerate return carries extra paragraphs | tester.md:198, :211-217 |
| E7 | seg-2 | driver | final message is prose, not the Summary block | run-package/SKILL.md:278-281 |
| E8 | seg-2 | driver | spec-change cause, suite time and test count read and relayed from return bodies | run-package/SKILL.md:28-31, :224-225 |
| E9 | U05 | agent | return is a mid-gate message; the run was interrupted | implementer.md:550 |

Warnings: U01 27-line return; U02 file names under the section path and a one-off memory file; U04 mkdocs/pylint claims from tailed output; the financialaudit implementer ran after its spawn was rejected (unsettled).

## Verdict

Does not conform: 9 ERROR (7 agent, 2 driver), 5 WARN, 12 NOTE. E1 and E2 came from the gate that could not go green on other sections' tests; HEAD (2.0.0) has since added `ELSEWHERE`/`TIMEOUT` rows, the clearer `let through` wording and a re-sent post-gate return, so those are changed since 1.0.0. E3 to E8 are still at HEAD as rules; E3, E5, E6 are agent faults, E4 (no new-section exception), E7 and E8 (no Summary field for a gate warning) suggest definition edits.
