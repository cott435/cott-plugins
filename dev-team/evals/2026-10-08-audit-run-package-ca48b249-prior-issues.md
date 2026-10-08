# Audit of a real `/dev-team:run-package data` run (quant-rebuild, session ca48b249), checking the recorded 2.9.0 fixes

**Tested against:** dev-team 2.9.0, tag `dev-team-v2.9.0` (`4cabb1e`), as installed in the plugin cache · model: `claude-opus-5-5` (the run's model; auditors ran on Sonnet 5.5) · 2026-10-08
**Set:** none — audit of a real run · **Pass rate:** n/a

## What was tested

Whether the fixes `4cabb1e` made for the 96a768ee audit (recorded in the ledger as attempt 1 of DT-028, 029, 031, 032, 034, 035, 040, 045, 046, 048, 052, `fixed_in` 2.9.0) hold in a real 2.9.0 run. This is `plugin-dev:audit-run` (0.16.0) on session ca48b249, which ran 2.9.0; it is an audit of a real run, not a set eval.

## Method

Session `ca48b249-07f7-4363-ac64-0ceb87a717d7`, project `/Users/connorott/PycharmProjects/quant-rebuild`. Selection `risk`: U01, U02, U05, U07, U10, plus the driver segment and a cross pass: 7 auditors, each given the prior issues whose `applies_to` names its agent type or `driver:run-package`. The plugin root is a cache copy with no git directory, so each issue was testable by version (run 2.9.0, `fixed_in` 2.9.0). `agent:researcher` has no unit in this run, so DT-048 went to no auditor. Every ERROR was spot-checked against the trace; every held and recurred verdict was opened at its step. The 2026-10-07 findings were kept in the scratchpad and replaced by this pass's; findings that match an issue the 2026-10-07 audit of this same session had already filed were marked seen and not logged a second time.

## Results

new: DT-053, DT-054, DT-055, DT-056, DT-057, DT-058; seen again: DT-002 (a new sighting, `D20`); prior: held DT-028, DT-032, DT-035, DT-052; recurred DT-031, DT-034; not exercised DT-029, DT-040, DT-045, DT-046, DT-048; not testable none.

## Verdict

Does not conform: 8 ERROR (7 agent, none definition), 3 WARN, 17 NOTE. The fixes mostly hold where the run exercised them: the tester's scoped `git status` (DT-032), the driver's stop wording (DT-028), the intent suite before the first write (DT-035) and the shared-file commit (DT-052). Two recurred: the implementer's FIX return is 24 lines against the cap (DT-031; the cap itself is DT-008) and the `TODO(decision` sweep runs only before the README edits (DT-034). Definition findings still at HEAD: DT-008, DT-016–DT-027, DT-055–DT-058. Two ERRORs and one NOTE half from the unit audit of U10 were dropped on spot-check: D6–D11 were `decided` when the designer read the ledger. The 2026-10-07 findings DT-004, DT-009–DT-011 and DT-014 were not found again by this pass's auditors.

Report: audits/runs/2026-10-08-ca48b249.md
