# audit-run — trace.py and run-auditor on a planted fixture, then on a real 55-agent run

**Tested against:** uncommitted, see the working-tree diff on branch `audit-run` (off `4def96d`): `skills/audit-run/`, `agents/run-auditor.md`, `evals/fixtures/audit-run/make_session.py` · model: `claude-opus-5-5` · 2026-09-28
**Set:** `evals/sets/audit-run.json` evals 1, 2 · **Iteration:** none, run by hand in the building chat · **Baseline:** none, a new skill · **Pass rate:** eval 1 6/6, eval 2 8/8

## What was tested

- **Eval 1.** `trace.py` rebuilds everything the audit needs from Claude Code's transcripts, and claims nothing they do not show.
- **Eval 2.** A `run-auditor` holding that trace against the plugin's files finds each planted defect as an ERROR, with a trace step and a rule line.
- **Real run.** The whole skill procedure produces findings on a real run whose evidence holds up.

## Method

- **Eval 1: mechanical.** `make_session.py` writes a toy plugin (`ship` skill, `writer` agent) and one session shaped like Claude Code's transcripts, with five planted defects:
  - P1: a write outside `out/`.
  - P2: "4 passed" claimed where pytest printed 1 failed.
  - P3: a failed commit plus another agent's HEAD reported as the writer's commit.
  - P4: a first line of `Done.` instead of `Result: done`.
  - P5: the driver writes a file.

  A script checked six facts in `index.json`, `units/U01.md` and `driver/seg-1.md`.
- **Eval 2: behavioral.** Two auditors on that trace, `unit` and `driver`, run as `general-purpose` agents told to follow `agents/run-auditor.md`. The agent is not installed from the branch, so this is a proxy for `plugin-dev:run-auditor`, and its broader tool list was not exercised.
- **Real run.** dev-team's `run-package data` on the `quant` repo, session `1493ed56`, with 55 units. Four units named plus the driver segment and a cross pass made 6 auditors. The findings are logged in `dev-team/evals/2026-09-28-audit-run-package-1493ed56.md`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 1 · index | root, version, 1 segment, U01 at D3 | as expected | ✅ |
| 1 · P1 | `notes/scratch.md` under Files written | present | ✅ |
| 1 · P2 | pytest step ERROR with "1 failed, 3 passed" | present | ✅ |
| 1 · P3 | abc1234 only as COMMIT UNCONFIRMED | `?abc1234`, never a plain COMMIT | ✅ |
| 1 · P4 | return begins `Done.` | yes | ✅ |
| 1 · P5 | driver Write at D5 | yes | ✅ |
| 2 · P1–P4 | four unit ERRORs with step + rule | F1–F4 ERROR, each citing the right `U01.S<n>` and `writer.md:<line>` | ✅ |
| 2 · P5 | driver ERROR for the Write | seg-1 F1 ERROR, `ship/SKILL.md:13` | ✅ |
| 2 · malformed return | driver took the done branch on `Done.` | seg-1 F2 ERROR | ✅ |
| 2 · no false ERROR | every ERROR's evidence holds | held. U01 F6 (the commit command differs from the prescribed one) is strict, but the evidence holds | ✅ |
| 2 · return | one `Findings:` line | both | ✅ |
| Real run | findings with evidence that holds | 30 ERROR written, 0 dropped on spot-check of every rule line and 9 trace checks; one line citation off by one | ✅ |

## Found while building, fixed before these results

- **Wrong commit attribution.** A `git log --oneline` after a quiet commit was being read as the agent's commit. In the real run, parallel researchers' commits failed (pathspec) and HEAD was a sibling's. Such commits are now marked `?sha` and confirmed only when the commit holds a file the unit wrote.
- **Forked-skill misdetection.** Preloaded skills made every agent look like a forked skill. A unit is now treated as a forked skill only when its first event is a skill body.
- **Unfinished units counted as finished.** Units still running counted as finished; now a unit is finished only on a hand-back or on its parent's tool result.
- **Risk selection noise.** Free-text returns were flagged as outliers against each other. The return's shape now ignores free text.

## Verdict

The claim held on both evals and on the real run. It is not proven for the installed agent (`plugin-dev:run-auditor` with its restricted tools), or for `--units new` watching a live run. Rerun eval 2 as the installed agent once `audit-run` ships.
