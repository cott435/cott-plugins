# `phases.py checks` — a phase's mechanical gate in one call, and `finish` behind it

**Tested against:** uncommitted — see working-tree diff, on `545b56d` (`scripts/phases.py`, `skills/run-phase/SKILL.md`, `skills/plan-phases/SKILL.md`, `templates/phases/overview.md`) · model: none · 2026-10-10
**Set:** `python3 evals/fixtures/phases/check.py` (50 cases, 10 of them new) · **Iteration:** none · **Baseline:** none · **Pass rate:** 50/50 cases; the real plan's gate 3 of 3 in one call

## What was tested

Why a phase of dev-team's determinism plan took 21 to 23 minutes with mechanical rows only,
read from the session transcripts of phases 20 and 21 (session `740962f9`), and whether one
command removes the part of it that was waiting:

1. `phases.py checks` runs `check-contracts`, `build-site` and the commands on the overview's
   `**Checks:**` line in one call, prints one line per command with a failure's FAIL lines
   under it, and exits 1 when any failed, timed out or could not start.
2. `phases.py finish` refuses a plan that has a `**Checks:**` line until `checks` has passed
   on the tree as it stands, and still commits when only the note, the ledger and the eval
   log changed after it.
3. A plan with no `**Checks:**` line is finished exactly as before.
4. `finish --log` takes a log's bare name.

## Method

No model. The transcripts first: each agent's tool calls with their gaps, from the two
subagent files under the session. Then `check.py`, which now builds its toy repo twice: the
four-phase plan as before, and the same plan with
``**Checks:** `python3 scripts/x.py` · `python3 scripts/y.py` `` and a `contracts.yml`. Then
the script on a scratch clone of `dev-team-determinism` at `4c32095` (phase 21), with
``**Checks:** `python3 evals/fixtures/check_all.py` `` added to its overview:
`brief --phase 22`, `checks determinism`, and `checks_stand` afterwards. The live worktree
was not touched. One negative run: `checks_stand` made to return true when a record exists,
which must fail the cases that depend on it.

## Results

What the transcripts show, per phase:

| | Phase 20 | Phase 21 |
|---|---|---|
| Wall time | 21.5 min, 121 turns, context up to 358k tokens | 23 min, 61 turns, up to 245k |
| Reading before the note | 8.5 min, about 55 turns, one call a turn | about 6 min |
| The edits | 1.5 min | about 2 min |
| `check_all.py` | 9.5 min: a foreground run cut off at the 120 s default and left running, a second run started beside it, 21 polling calls, then a blocking wait | 14 min: cut off at 120 s; finished `575/575` at 18:09; a wait on `pgrep -f "evals/fixtures/check_all.py"` then matched its own shell and ran to its 590 s timeout |
| Did the agent read the full run's result | yes (`526/526 pass`) | no: no tool result holds `575/575`; the log's figure is 526 + 49. The run's output file does say `575/575 pass`, exit 0 |

`check_all.py` alone, on a copy of `3495742`, one tree at a time: `state-cases` 153 s (236
cases), `hook-events` 128 s (255), `locked` 6 s, the rest 2 s. About 290 s, every case in
series.

| Case | Result | Pass |
|---|---|---|
| `brief` with a `**Checks:**` line: the one command, what it runs, the foreground timeout | as written | yes |
| `finish` before `checks` | exit 1 with the command | yes |
| `checks` with a failing command | exit 1; `FAIL c` and its detail printed, its other output only in `checks.log`; the other two PASS, the passing command's last line beside it | yes |
| `finish` after failed checks | exit 1 | yes |
| `checks` all passing | exit 0, `checks: 3 of 3 pass` | yes |
| `finish` after an edit made since `checks` passed | exit 1 | yes |
| `finish` after `checks`, then the note, the eval log and its index row; `--log` a bare name | committed, tree clean | yes |
| a command over `--timeout` | exit 1, `timed out after 1s` | yes |
| a command that cannot start | exit 1, `could not start` | yes |
| a plan with no `**Checks:**` line, no contracts, no site | exit 0, `no checks here`; its `finish` cases unchanged (the 40 earlier cases) | yes |
| negative: `checks_stand` true whenever a record exists | 47/50: the three cases that need a failed or stale record fail | yes |
| the determinism plan: `brief --phase 22` | names `check-contracts`, `build-site`, `python3 evals/fixtures/check_all.py` | yes |
| the determinism plan: `checks determinism` | `PASS check-contracts (0s): 73/73 pass`, `PASS build-site (0s)`, `PASS python3 evals/fixtures/check_all.py (292s): 575/575 pass`; one call, 4 min 53 s; `checks_stand` true in 0.1 s | yes |

`check-contracts` 15/15 and `build-site` clean on plugin-dev itself.

## Conclusion

Held. One call replaces what cost phase 20 two runs and 21 polls and phase 21 a ten-minute
dead wait, and `finish` no longer takes the suite's result on the agent's word.

Not tested: a phase agent following the new `run-phase` text. The claim that it makes the
one call with `timeout: 600000` and does not poll is unproven until a phase runs on this
version. Not changed here: `check_all.py` still takes 292 s, which is dev-team's to shorten;
the reading before the note, which the new sentence in `run-phase` asks to batch and nothing
enforces.
