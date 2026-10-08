# Re-audit of a real `/dev-team:run-package data` run (quant-rebuild, session ca48b249), reusing the 2026-10-07 findings

**Tested against:** dev-team 2.9.0, tag `dev-team-v2.9.0` (`4cabb1e`), as installed in the plugin cache · model: `claude-opus-5-5` (the run's model; the reused findings were written by the 2026-10-07 auditors) · 2026-10-08
**Set:** none — audit of a real run · **Pass rate:** n/a

## What was tested

`/dev-team:run-package data` on the quant-rebuild `data_rebuild-profiler-rerun2` branch (2026-10-07): 12 spawned agents and one driver segment. This is `plugin-dev:audit-run` (0.16.0) run a second time on a session that was already audited and seeded into the ledger, to exercise the new ledger comparison against earlier runs. It is not a set eval.

## Method

The user chose to reuse the existing audit rather than re-spawn auditors: no auditor ran. The trace was rebuilt (`trace.py build`, 12 units, 62 driver steps) and `flow.html` re-rendered; the seven findings files from 2026-10-07 (seg-1, cross, U01, U02, U05, U07, U10) were read as they stood. All 13 ERRORs were re-spot-checked against the rebuilt trace (U05.S13/S22–S25, U07.S10–S20, U10.S42/S43/S57/S62, D18–D50, and the quoted rules by `grep` in the working tree). Every cited rule quote is still in the working tree, and `git log dev-team-v2.9.0..HEAD -- agents skills hooks` is empty, so HEAD's definitions are the ones that ran. The ledger holds no `fixed` issue (all 52 are `open`), so there were no prior-issue checks; `issues.py check` printed `ok: 52 issues`. No `seen` lines were written: each finding is already a Found in line of DT-001–DT-027 for this session, and appending it again would count one sighting twice. No new run report was written, because the 2026-10-07 report is this audit's report.

## Results

new: none; seen again: none (all 27 issues, DT-001–DT-027, are already recorded for this session); prior: held none, recurred none, not exercised none, not testable none.

Comparison with the 96a768ee audit (dev-team 2.8.0, the run before this one in time), read off the trace and not formally verified, since none of its issues has a recorded fix:

- Same issue appears in both runs: DT-001 (rows not printed after a re-derive), DT-003 (re-derive skipped after a cap answer), DT-021 (no `stopped because` entry for a user stop). DT-031's class (an implementer return that breaks its cap or closed shape) shows up again as U07 F1/F2 (DT-008, DT-009).
- 96a768ee issue with no sign in this run, where the run exercised the agent: DT-032 (U02.S23 scopes `git status` to its paths), DT-035 (U07.S25 runs the intent suite before the first write at S40), DT-041 and DT-042 (U02.S10 lists only its own directories; its reads stay inside the allowed set), DT-037 (no `--amend` in any unit).
- Not exercised: DT-029 (one implementer ran, no parallel pair), DT-034, DT-036, DT-038, DT-039, DT-040, DT-043 and the 96a768ee definition NOTEs, which need an agent or a branch this run's 5 selected units did not cover.

## Verdict

Does not conform, unchanged from the 2026-10-07 report: 13 ERROR (12 agent, 1 definition: DT-008), 2 WARN, 13 NOTE. Definition findings still at HEAD: DT-008, DT-016–DT-027. All 13 ERRORs held on re-spot-check; none dropped.

Report: audits/runs/2026-10-07-ca48b249.md
