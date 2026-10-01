# Audit of a real `plan-package engine` → `run-package engine` run (session b05b2879)

**Tested against:** `07dcb19` (tag `dev-team-v2.3.0`), which ran every run-package unit. U01, the forked `plan-package` architect, ran on `b82757f` (tag `dev-team-v2.2.0`). · models: `claude-fable-5-1`, `claude-opus-5-5` · 2026-10-01
**Set:** none, since this audits a real run rather than a set eval · **Auditors:** `plugin-dev:run-auditor` via `/plugin-dev:audit-run` (plugin-dev 0.14.0)

## What was tested

This checks whether dev-team's workflow behaved as its own files say it should across one full real run. The chat ("Plan package engine") ran `/dev-team:plan-package engine`, then `/dev-team:run-package engine`, which built all 11 sections of `engine` and closed the package.

## Method

- **Session:** `b05b2879-3f25-4041-817b-3c06d28efb38`, project `~/PycharmProjects/wild-ones`, branch `design`, 2026-10-01 02:48 → 08:16 UTC, 74 agent units and 256 driver steps.
- **Trace:** built with `audit-run`'s `trace.py` into `evals/workspace/audit/b05b2879/`, which is gitignored.
- **Selection:** the `risk` pick of 12 units (hook blocks and odd returns), plus five units the user approved adding: U01 (plan-package architect), U03 (first designer), U09 (first reviewer), U34 (PLAN architect) and U74 (close architect).
- **Auditors:** 17 unit auditors, 1 driver auditor (seg-1) and 1 cross auditor, 19 in all.
- **Spot-check:** every ERROR was checked against its trace step and its rule line, and none was dropped.
- **Merging:** unit findings covered by a systemic `cross` or `seg-1` finding were merged into it, and the systemic severity was kept.
- **Full report:** `evals/workspace/audit/b05b2879/report.md`. It is gitignored, so this entry carries the findings.

The trace script listed U01 as "still running" because it is a forked-skill unit. It had in fact finished with `Result: done` and commit `1bc1e7a`.

## Results

**Totals after merging:** 17 ERROR · 21 WARN · 29 NOTE. As filed, the auditors reported 39 · 28 · 57.

| Id | Unit | Fault | Finding | Rule |
|---|---|---|---|---|
| E1 | U43, U71, U40 | definition | A `Result: blocked` or let-through amendment sent after the stop gate never reaches the driver: the harness delivers only the first `SubagentHandback`. The driver reviewed two blocked sections and reported "11/11 DONE" | `agents/implementer.md:462-464`, `skills/run-package/SKILL.md:250-264` |
| E2 | U71 + README authors | definition | The package shipped with `status.py --surface` failing. READMEs grouped names in a row, and the parser reads only the first backticked name | `agents/implementer.md:516` vs `skills/status/scripts/status.py:1313-1318` |
| E3 | 9 units, all roles | definition | Closed return lists were broken in 9 units. Implementer steps 4 and 10 send Security and Size lines to a return list that has no line for them | `agents/implementer.md:733` vs `:343`, `:356`, `:431`; `architect.md:616`; `tester.md:266` |
| E4 | seg-1 (U03) | driver | `Skills to invoke: —` instead of `none` in all 15 designer spawns | `skills/run-package/SKILL.md:66` |
| E5 | seg-1 | driver | Changed rows were not printed after 7 of 31 re-derives | `skills/run-package/SKILL.md:272-274` |
| E6 | U01 | agent | The plan-package survey read past its list and ran `python3 -c` | `skills/plan-package/SKILL.md:43-51` (2.2.0) |
| E7 | U05 | agent | The D3 xfail reason landed off the decorator line after `ruff format` | `agents/tester.md:120` |
| E8 | U06 | agent | The `Tests:` per-heading counts sum to 127, not the 133 claimed | `agents/tester.md:274` |
| E9 | U08, U16 | agent | The README's Implementation notes name no skill rules | `agents/implementer.md:337` |
| E10 | U09 | agent | A silent deviation was graded WARNING and the verdict was approve | `agents/reviewer.md:161-162` |
| E11 | U26 | agent | The tester ran `python3 -c` | `agents/tester.md:50` |
| E12 | U27 | agent | "No document covers it" was false: the heal formula covers the case | `agents/tester.md:143-145` |
| E13 | U34 | agent | "Project skills: none" was returned with no listing behind it | `agents/architect.md:162` |
| E14 | U34 | agent | The architect grepped the whole plugin cache, `evals/` included | `agents/architect.md:36` |
| E15 | U40 | definition | The stop gate counts a rewritten assert as a "removed assert" | `hooks/gate_on_stop.py:508-513` |
| E16 | U40 | agent | Step 0 reads ran out of order | `agents/implementer.md:286-289` |
| W1 | U05, U27 (+3) | definition | `test-driven-development` is said to be preloaded but is missing from the tester frontmatter | `agents/tester.md:7-10` vs `:168` |
| W2 | 9 units | definition | "Read every document" was met with greps and ranged reads | `tester.md:166`, `designer.md:176`, `implementer.md:77`, `reviewer.md:200` |
| W3 | U06, U27, U34, U74 | definition | Shell `rm` and `cp` wrote to the repo, and the Bash guard doesn't cover them | `hooks/guard_bash.py:4-8` vs `tester.md:54-55`; `architect.md:350-351` |
| W4 | U28, U29, U57 | definition | A contract signature that fails the repo's lint was filed as a `deviation`, which cost a PLAN plus 11 agent runs | `agents/implementer.md:636-641` |
| W5 | U08, U16, U66 | definition | Integration tests are designed but cannot be written under `tests/integration/` | `agents/implementer.md:415` vs `designer.md:229` |
| W6 | U06 → 11 units | definition | A tester's lint failure was carried as ELSEWHERE for about 65 runs and never asked of the user | `agents/tester.md:63-73` |
| W7–W21 | U01, U05, U09, U16, U27, U28, U34, U57 | agent ×14, definition ×1 | Single-unit warnings: contract over its line budget, listing the package root, a stale memory note, shell commands outside the allow-list, nine modules written before any test run, and others (see the report) | — |

## Verdict

Not clean. By fault, the 17 ERRORs are 4 definition, 2 driver and 11 agent. Of the 21 WARNs, 7 are definition and 14 are agent.

These definition findings are still at HEAD (`07dcb19` is HEAD):

- **E1:** a `Result: blocked` sent after the stop gate never reaches the driver. 2.3.0's "amendment as final text" fix for the befb4798 audit does not work under this harness.
- **E2:** the surface README format.
- **E3:** the closed return lists. The befb4798 and 9ecf4176 audits also found this.
- **E15:** the gate's removed-assert check.
- **W1–W6.**

No edits have been made in response yet.
