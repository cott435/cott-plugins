# O — the plan-and-review loop gets an exit, the spine is synced before completion, cross-cutting facts propagate

**Tested against:** `ca31fb3` (0.5.2) with the fixes uncommitted on branch `plan-loop-exit` —
see the working-tree diff: `skills/status/scripts/status.py`, `agents/reviewer.md`,
`agents/architect.md`, `agents/designer.md`, `skills/review-plan/SKILL.md`,
`skills/plan-package/SKILL.md`, `skills/run-package/SKILL.md`,
`skills/planning-templates/references/integration.md`, `contracts.yml` · model:
`claude-sonnet-5` (headless runs; `claude-fable-5-1` ran the checks) · Claude Code `2.1.270` ·
2026-09-22

## What was tested

A user's twelve-section package went through six consecutive `request changes` plan reviews:
each re-plan fixed every prior finding and added about two, because one cross-cutting fact (an
asset class on a different exchange calendar) was patched only in the sections the last review
named, and because the spine's design was never synced after its build. Three fixes:

1. **Round counting and a stop.** `status.py <pkg> --plan-rounds` derives the consecutive
   `request changes` plan reviews since the last approving one; the reviewer writes `Round:`
   and, from round 2, `Convergence: <k> prior unfixed, <m> new`, counts a fact still assumed
   by an unreached section as *unfixed: incomplete propagation*, and on round 2 with a prior
   finding unfixed (or as many new as before), or on round 3, stops the loop with a two-command
   choice; `--defer` moves the standing findings to their sections and approves with fixes.
2. **Spine sync before completion.** `run-package` spawns `sync-design` between the spine's
   review and the completion `plan-package`; the architect's completion run checks each built
   section's design for an **As shipped** citing its last commit and syncs it inline otherwise.
3. **Propagation.** The reviewer files a cross-cutting finding once with `touches:`; the
   architect greps for the fact, records the union under integration.md's **Propagation**, and
   re-delegates every section on it with `Propagate:`.

Also fixed on the way: the reviewer's previous report was "newest by date, excluding today's",
so every same-day re-review compared against nothing; and a plan review's diff range omitted
`docs/decisions.md` and `docs/followups.md`, where a plan finding is often answered.

## Method

**Mechanical.** A scratch git repo with a one-section plan and plan reports written by hand,
eight states, reading `status.py data --plan-rounds`, `--plan-gate` and the `plan:` line. The
new `contracts.yml` forbid claim run on the real files and with a bare "on `request changes`,
`/dev-team:plan-package`" sentence planted in `review-plan`.

**Behavioral.** A fixture repo on a feature branch: package `data`, three sections, a round-1
plan report whose one CRITICAL is the calendar fact with `touches: ingest, clean`, followed by
a re-plan commit that corrected the contract and `ingest` only — `clean`'s design still drops
non-NYSE days — with the follow-up ticked and **Propagation** listing `ingest` alone. Real
headless runs, `claude -p "<command>" --plugin-dir <worktree>/dev-team --model claude-sonnet-5
--output-format stream-json --verbose --permission-mode bypassPermissions`:

- O1: `/dev-team:review-plan data` on the fixture. Expected: `Round: 2`; the calendar finding
  classified unfixed as incomplete propagation naming `clean`, once; a `Convergence:` line;
  `request changes`; return line 3 `Loop: stopped`; the two-command block.
- O2: `/dev-team:review-plan data --defer` on O1's result. Expected: no re-review; each open
  `data/plan` entry ticked `deferred to …` and copied to its section(s); a report with
  `Verdict: approve with fixes` and a **Deferred** heading; `--plan-gate` passes;
  `--plan-rounds` reads 0; the section rows count the copies as review-sourced follow-ups.

The architect side (stale-spine sync on a completion run, `Propagate:` fan-out) was not run
headless: it needs a built spine and a designer fan-out, and the change is a classification
row plus a delegation line read by the same agent that already handles `Review findings:`.
Recorded here as untested; the next real completion run under the driver is the check.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| M0 no plan reports | rounds 0 | 0 | ✓ |
| M1 one `request changes` | 1 | 1 | ✓ |
| M2 two, on different days | 2 | 2 | ✓ |
| M3 `approve with fixes` newest | 0 | 0 | ✓ |
| M4 three same-day `-2`/`-3` after the approve | 3 | 3 | ✓ |
| M5 `--plan-gate` verdict line | carries `(round 3; not converging …)` | as expected | ✓ |
| M6 `plan:` line | `…; 3 request-changes round(s) since last approve` | as expected | ✓ |
| M7 no `docs/reviews/` | 0, exit 0 | 0 | ✓ |
| M8 `--plan-rounds` with no package | usage line, exit 2 | as expected | ✓ |
| C1 forbid claim, real files | PASS | PASS, 26/26 | ✓ |
| C2 forbid claim, planted sentence | FAIL at `skills/review-plan/SKILL.md:<line>` | FAIL at `:99` | ✓ |
| O1 `review-plan data`, round 2 | `Round: 2`; calendar fact unfixed as incomplete propagation naming `clean` once; `Convergence:`; `request changes`; `Loop: stopped`; the block | `Round: 2`, `Convergence: 1 prior unfixed, 0 new`, one CRITICAL at `design/clean.md#2,#3,#4,#5,#7` worded *unfixed: incomplete propagation of the prior finding*, `touches: clean`; **Carried** left empty with the reason; `Loop: stopped`; the block with both commands; one `data/plan` follow-up; commit `27f1043` with the trailer. $0.41 | ✓ |
| O2 `review-plan data --defer` | no re-review; entry ticked `deferred to …` and copied to `data/clean`; `approve with fixes` + **Deferred**; gate passes; rounds 0; `clean` row counts it | The `data/plan` entry ticked `… deferred to data/clean`; a `data/clean` copy with the `— review 2026-09-22, see …-plan-2.md` tail; `2026-09-22-data-plan-3.md` with `Verdict: approve with fixes`, `Round: 3`, **Deferred**; only the report and `docs/followups.md` in commit `70efad5`, trailer `review-plan data --defer`; `--plan-gate` PASS, `--plan-rounds` 0, `clean` row `1 (1 review, 0 intent)`. $0.26 | ✓ |

## Verdict

Holds, 13/13. The round counter is derived correctly across days, same-day suffixes and an
approve reset; the forbid claim fails on the planted sentence; the round-2 review classifies a
half-propagated fact as one unfixed finding rather than a fresh CRITICAL, stops the loop with
the two-command choice, and `--defer` moves the finding to its section and reopens the gate
without a re-review.

Two watch items, neither fixed by a re-run here:

- O1's return opened with a sentence before `Result: done` ("Report and follow-up filed,
  committed at …"). The driver branches on line 1, so the **Return message** rule now says
  the sentinel is the first characters of the return with no sentence before it. O2, run
  after that edit, began with `Result: done`.
- O2 wrote no `Loop:` line. The rule says every plan-mode return carries one, `converging` on
  an approving verdict included; the driver never spawns `--defer`, so nothing branches on it,
  but the omission is a real deviation from the prompt.
- Untested: the architect's completion-run stale-spine sync and the `Propagate:` fan-out.
  Both are mechanical additions to steps the same agent already performs; the next real
  completion run under `/dev-team:run-package` is the check, and its `sync-design` spawn is
  what makes the inline path normally a no-op.
