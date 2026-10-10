# `phases.py checks` and a fuller `brief` — a phase's mechanical gate in one call, its items with their cited lines in one output

**Tested against:** uncommitted — see working-tree diff, on `545b56d` then `3b51457` (`scripts/phases.py`, `scripts/edits.py`, `skills/run-phase/SKILL.md`, `skills/plan-phases/SKILL.md`, `templates/phases/`) · model: none · 2026-10-10
**Set:** `python3 evals/fixtures/phases/check.py` (56 cases, 16 of them new) · **Iteration:** none · **Baseline:** none · **Pass rate:** 56/56 cases; the real plan's gate 2 of 2 in one 82 s call

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
5. `edits.py show --located` carries every `path:line` an item cites from the reviewed commit
   to the tree as it stands, and `phases.py brief` prints the phase's items that way, with the
   edit list's Goal, Decisions taken and What must not break, so a phase's chat reads one
   output where it made about fifty reads.
6. `checks` builds the site at the plan's last phase and at no phase before it.

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
| `brief` against an edit list | the phase's item whole, the lines it cites under it, no other phase's item; `--short` leaves the part out | yes |
| `show --located`: a range moved by two added lines; a line an edit replaced; an untouched line; a file that is gone; a bare path | `:1-2 → :3-4, moved`; `:4 → :6, changed since the review` with the line there; `:4 → :4, as reviewed`; `the file is gone`; nothing | yes |
| `show --located --at HEAD`; `show` without `--located` | carried from the commit given; the item only | yes |
| `brief` at phase 1, and at the last phase, of a plugin with a `site/site.yml` | no `build-site` among the checks; `build-site` among them | yes |
| `checks` before the last phase; at the end of the plan | the site not built; `PASS build-site`, `site/docs/` written, the tree clean | yes |
| negative: `checks_stand` true whenever a record exists | three cases fail, the ones that need a failed or stale record (run when the set was 50) | yes |
| the determinism plan: `brief --phase 22` | names `check-contracts`, `build-site`, `python3 evals/fixtures/check_all.py` | yes |
| the determinism plan: `checks determinism` | `PASS check-contracts (0s): 73/73 pass`, `PASS build-site (0s)`, `PASS python3 evals/fixtures/check_all.py (292s): 575/575 pass`; one call, 4 min 53 s; `checks_stand` true in 0.1 s | yes |

| the determinism plan: `brief --phase 22`, `23`, `30`, `37` at `4c32095` | 57, 57, 85 and 33 KB; 39, 47, 82 and 6 cited places carried from `e8df7f8`, the commit the list's opening paragraph names last; of phase 23's 34 cited places on three items, 18 moved, 13 changed, 3 as reviewed; `agents/architect.md:426-430 → :400-404` is the same paragraph | yes |
| the determinism plan with dev-team's `check_all.py` run in parallel (`7f24905`) and `build-site` left to phase 37 (`249af7c`): `checks determinism` | `PASS check-contracts (1s): 73/73 pass`, `PASS python3 evals/fixtures/check_all.py (82s): 575/575 pass`; one call, 82 s | yes |
| `edits.py check` and `coverage` on the determinism list | `ok: 152 items, 23 decisions`; `ok: 152 items in 37 phases` | yes |

`check-contracts` 15/15 and `build-site` clean on plugin-dev itself.

## Conclusion

Held, for what a script can show. One call replaces what cost phase 20 two runs and 21
polls and phase 21 a ten-minute dead wait; with dev-team's runner in parallel that call is
82 s, where the gate took those phases 9.5 and 14 minutes. `finish` no longer takes the
suite's result on the agent's word. The brief now holds what the phase 20 agent fetched over
about fifty turns: the spec's three sections, the items, and each cited place as it stands.

Not tested: a phase agent on this version. That it makes the one `checks` call with
`timeout: 600000` and does not poll, and that it reads less because the brief holds more, are
both unproven until a phase runs; the eight minutes of reading in phase 20 also held the
agent's own thinking, which no brief removes. A place marked *changed since the review*
points at the start of what replaced the line, which may not be where the text went.
