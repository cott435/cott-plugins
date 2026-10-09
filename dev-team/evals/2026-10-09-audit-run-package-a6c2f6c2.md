# Audit of a real `/dev-team:run-package data` run (quant-rebuild, session a6c2f6c2)

**Tested against:** dev-team 2.11.0, release commit `2634539` (no `dev-team-v2.11.0` tag exists), as installed in the plugin cache and identical to the working tree for `agents/`, `skills/` and `hooks/` · model: `claude-opus-5-5` (the run's model) · 2026-10-09
**Set:** none — audit of a real run · **Pass rate:** n/a

## What was tested

`/dev-team:run-package data` on the quant-rebuild `profiler-rerun3` branch (2026-10-08 21:33 to 2026-10-09 13:22): 17 spawned agents and one driver segment, stopped by the user at identity IMPLEMENT. This is `plugin-dev:audit-run` (0.16.0) on a real run, with all 40 fixed issues in the ledger checked as prior issues. It is not a set eval.

## Method

Session `a6c2f6c2-2a02-4c32-8c15-41462f06288a`, project `/Users/connorott/PycharmProjects/quant-rebuild`. `trace.py build` gave 17 units and 88 driver steps. `--units risk` with `--cover` for every `applies_to` entry chose 9 of 17 units (U01, U02, U05, U07, U10, U11, U12, U13, U15), the driver segment, and a cross pass: 11 `run-auditor` agents, ten in parallel and the cross auditor after them. All 40 fixed issues were testable by version (the plugin root is a cache copy, not a git checkout; the run version 2.11.0 is at or above every `fixed_in`); `agent:researcher` was uncovered, so DT-048 went unchecked. Spot-checks: the 3 ERRORs against `U01.json`, `U11.json` and `U13.json` and the quoted rules; the 4 recurred verdicts against `driver/seg-1.md`; most held verdicts against the unit JSON and the project's git history. Four verdicts changed on spot-check (listed in the run report). The U15 hand-back message said 1 ERROR; its findings file has a WARN, and the file was used.

## Results

New: DT-059–DT-078; seen again: DT-036, DT-037, DT-050, DT-057; prior: held DT-005, DT-008, DT-009, DT-010, DT-011, DT-013, DT-014, DT-016, DT-018, DT-020, DT-021, DT-023, DT-024, DT-025, DT-027, DT-028, DT-031, DT-032, DT-034, DT-045, DT-052, DT-055, DT-056, DT-057, DT-058; recurred DT-001, DT-002, DT-019, DT-022; not exercised DT-003, DT-004, DT-006, DT-012, DT-026, DT-029, DT-035, DT-040, DT-046, DT-048, DT-053; not testable none. The findings are in the committed run report.

## Verdict

3 ERROR (profiler scratchpad `COPY`, tester `sed -i`, architect return shape), 10 WARN, 14 NOTE; by fault, 13 `definition` findings, all still at HEAD, and the rest `agent` or `platform`. Four prior issues recurred, all on the driver (`status.py` rows not printed before the next act, a `wc` on a repo file, a line-range Read of `docs/decisions.md`). Two of the four dropped-on-spot-check verdicts (DT-035 and DT-003/DT-006) point at Verify lines that need rewording.

Report: audits/runs/2026-10-09-a6c2f6c2.md
