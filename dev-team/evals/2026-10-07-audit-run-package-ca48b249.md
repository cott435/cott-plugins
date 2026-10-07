# Audit of a real `run-package data` run · session ca48b249

**Tested against:** dev-team 2.9.0, tag `dev-team-v2.9.0` (`d11c9a5`), run from the plugin cache `~/.claude/plugins/cache/cott-plugins/dev-team/2.9.0` · model: `claude-opus-5-5` (driver and every agent) · 2026-10-07
**Set:** none — an audit of a real run, not a set eval · **Baseline:** none

## What was tested

Whether the 2.9.0 driver and agents did what their definitions say during one live
`/dev-team:run-package data` session on `~/PycharmProjects/quant-rebuild`, branch
`data_rebuild-profiler-rerun2`. This was the first real run after the 2.9.0 fixes from the 96a768ee audit.

## Method

`/plugin-dev:audit-run latest` (plugin-dev 0.15.0) on session `ca48b249-07f7-4363-ac64-0ceb87a717d7`.
The run lasted 1h12m with 12 units in 6 waves: 4 profiler, 4 tester, 2 reviewer, 1 implementer and 1 designer. It ended at
identity IMPLEMENT on a user "stop when you can". Units were selected with `--units risk`, which picked 5:
U01 profiler, U02 tester, U05 reviewer, U07 implementer and U10 designer. With the driver segment and the cross check,
that made 7 `run-auditor` agents. Every ERROR was spot-checked against its trace step and rule line, and none was dropped.
Every `definition` finding was grepped in the working tree. The full report is
`evals/workspace/audit/ca48b249/report.md` (gitignored), with `flow.html` beside it.

## Results

| Id | Unit | Fault | Finding | Rule |
|---|---|---|---|---|
| E1 | seg-1 | agent | Changed rows not printed after 3 of 6 re-derives (D18, D25, D40) | `skills/run-package/SKILL.md:331` |
| E2 | seg-1 | agent | `docs/decisions.md` read with `grep`/`wc`/`sed` in Bash (D42, D48) | `skills/run-package/SKILL.md:47`, `:38` |
| E3 | seg-1 | agent | No `status.py` re-derive after the review-cap answer (D27→D30) | `skills/run-package/SKILL.md:427` |
| E4 | U01 | agent | Provenance credits this program's `pull()` for input pulled by another branch's program | `skills/planning-templates/references/data-profile.md:29` |
| E5 | U05 | agent | Reviewer ran `merge-base`, `branch --contains`, `git grep`, `ls-files`, `head`, `sed` | `agents/reviewer.md:107-118` |
| E6 | U05 | agent | Review report written without reading `review-report.md` | `agents/reviewer.md:510` |
| E7 | U05 | agent | Return's CRITICAL line paraphrases the report's | `agents/reviewer.md:570` |
| E8 | U07 | definition | 20-line return cap is unmeetable with one `Review:` line per item (13 items) | `agents/implementer.md:899-901` |
| E9 | U07 | agent | Two review items on one `Review:` line | `agents/implementer.md:900-901`, `:925` |
| E10 | U07 | agent | Step-0 reads out of order (review first; backlog before dependency READMEs) | `agents/implementer.md:316-319` |
| E11 | U10 | agent | Unlisted call-path frames logged as an additive deviation instead of `spec-change: contract` | `agents/designer.md:272`, `:345` |
| E12 | U10 | agent | Read another section's design (`ingest.md`) | `agents/designer.md:43` |
| E13 | cross | agent | U06 returned `to decide: 5`; the profile has 6 | `agents/profiler.md:130` |
| W1 | U10 | agent | Read a dependency's source (`yahoo/profiles.py`) | `agents/designer.md:43`, `:88` |
| W2 | U10 | agent | Design is 413 lines against a 100–250 target | `agents/designer.md:333` |

The 13 NOTEs, merged, are in the report. The systemic one is cross F2. `.dev-team/` artifacts from another
branch (profiler Store input, a gate record) were treated as this branch's, and that cost a full extra
audit cycle: the cap question, a fix round, a re-review and a test regeneration. It covers U01 F2, U05 F4 and U07 F6.

## Verdict

The run did not follow its definitions cleanly: 12 `agent` ERRORs and 1 `definition` ERROR. The 2.9.0
fixes for the 96a768ee findings held where they were exercised. U02, the tester, was clean.
`definition` findings still at HEAD:

- E8, the implementer's 20-line cap against per-item `Review:` lines;
- the other-branch-artifact gap (cross F2: `profiler.md:97`, `reviewer.md:158`, `implementer.md:883-884`);
- shell-read bans enforced only in prose (cross F3: `hooks/guard_bash.py`);
- `<d>` undefined in profile mode (cross F4, `profiler.md:130`);
- `docs/decisions.md` missing from the driver's Read list (`SKILL.md:38`);
- the 4-question `AskUserQuestion` limit against "one per block" (`SKILL.md:387`);
- no `stopped because` entry for a user stop (`SKILL.md:496`);
- the print-rows rule tied to "before the next spawn" (`SKILL.md:331`);
- the implementer's Inputs vs step-0 read order (`implementer.md:75-84`, `:318`);
- "read" undefined for a directory input (`implementer.md:74`);
- designer §10 silent on call-path frames (`designer.md:301`, `:316`);
- `stage` probe docs not named in the designer (`designer.md:103`);
- the designer's Write-only list omitting memory (`designer.md:25`).

Nothing has been changed in response yet.
