# P — the section and package loops get the same exit, and CRITICAL becomes a closed list

**Tested against:** `5db17e5` (main after eval O) with the fixes uncommitted on branch
`section-loop-exit` — see the working-tree diff: `skills/status/scripts/status.py`,
`agents/reviewer.md`, `skills/review-section/SKILL.md`, `skills/review-package/SKILL.md`,
`skills/review-plan/SKILL.md`, `skills/run-package/SKILL.md`, `contracts.yml` · model:
`claude-sonnet-5` (headless run; `claude-fable-5-1` ran the checks) · Claude Code `2.1.270` ·
2026-09-22

## What was tested

Eval O gave the plan loop an exit. The section loop that took a user's spine through five
build-and-review rounds had the same shape and two problems of its own: `run-package` counted
implementer runs in its own conversation, so every re-run started at zero and the manual
`implement-section` had no counter at all; and the section checklist left severity undefined
for items 3–8, so a fresh reviewer could grade a docstring CRITICAL and buy another build.

1. **One counter for every loop.** `status.py --rounds <pkg> | <pkg>/<section> |
   <pkg>/surface` replaces `--plan-rounds`; the reviewer runs it first in every mode; the
   driver branches on the reviewer's `Loop:` line instead of its own count; section rows and
   the `surface:` line carry ` r<n>` while non-zero.
2. **Rounds and convergence in every mode**, with `implement-section` / `finalize-package` as
   the fixing commands and `review-section` / `review-package --defer` re-filing the standing
   findings as `— noted` follow-ups (same owner, not counted by the finalize gate); a break or
   a failing check cannot be deferred.
3. **Severity is a closed list**: a break, a failing check, a wrong result on the main path, a
   security finding, the silence rules and bar-lowered. Everything else is WARNING. On a
   re-review, a wrong-result or security finding outside the diff is WARNING plus a `— noted`
   follow-up, so the set of blockers shrinks every round.

## Method

**Mechanical.** The eval-O scratch repo extended with a section README and section and
package reports, six states, reading `status.py --rounds` and the report rows. The widened
forbid claim on the real files and with a bare "on `request changes`,
`/dev-team:implement-section $section`" sentence planted in `review-section`.

**Behavioral.** A fixture repo on a feature branch: package `data`, one section `ingest`
with real code and two passing unit tests, plain `python3 -m pytest`, no import-linter, no
constraints. A round-1 report with one CRITICAL — `DataError("VENDOR_DOWN")` where the
contract names `VENDOR_UNAVAILABLE` — followed by a fix commit that changes only that code
and its test, with the follow-up ticked. Outside that diff, planted at build time: `_row`
silently drops any row with zero volume, which contract §7 and design §8 say to keep (a wrong
result, kind 3), and `_row` has no docstring (a WARNING under the closed list). One real
headless run, `claude -p "/dev-team:review-section data/ingest" --plugin-dir
<worktree>/dev-team --model claude-sonnet-5 --output-format stream-json --verbose
--permission-mode bypassPermissions`. Expected: `Round: 2`; the round-1 CRITICAL classified
fixed; `Convergence: 0 prior unfixed, 0 new`; the zero-volume drop reported as WARNING with a
`— noted` follow-up, not CRITICAL; the docstring a WARNING; `Verdict: approve with fixes`;
`Loop: converging`; return line 1 `Result:`.

P1 was run once with the change as first written, and again (P2, on a copy of the fixture
reset to the fix commit) after two edits P1 forced — see Verdict. Not run headless:
`--defer` in section form (the same procedure as eval O's O2 with a different tail), the
package-mode rounds, and the driver's `Loop:` branch. Eval O's `--plan-rounds` is now
`--rounds <pkg>`; O's entry records the flag as it was.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| S0 section, no reports | 0 | 0 | ✓ |
| S1 section, two same-day `request changes` | 2 | 2 | ✓ |
| S2 section row | reviewed column ends ` r2` | `… request changes @fd901fd r2` | ✓ |
| S3 `approve` newest | 0 | 0 | ✓ |
| S4 `<pkg>/surface` → `<pkg>-package` stem; `surface:` line | 1; ` r1` | 1; ` … request changes @4aa5594 r1` | ✓ |
| S5 `--rounds <pkg>` (plan) after `docs/reviews/` was recreated empty of plan reports | 0 | 0 | ✓ |
| S6 `--rounds` with no target | usage line, exit 2 | as expected | ✓ |
| C1 forbid claim, real files | PASS | PASS, 26/26 | ✓ |
| C2 forbid claim, planted sentence in `review-section` | FAIL at `skills/review-section/SKILL.md:<line>` | FAIL at `:95` | ✓ |
| P1 `review-section data/ingest`, round 2, first wording | see Method | `Round: 2`, `Convergence: 0 prior unfixed, 1 new`; the round-1 CRITICAL verified fixed; the zero-volume drop graded CRITICAL as a *kind-1 contract break* (contract §7 says such a bar is kept), so it kept its severity outside the diff by the rule as written; docstring and the `l` name WARNING, the comprehension SUGGESTION; `request changes`; then the round-2 "as many new as before" test fired and the return ended with the stop block. **No `Loop:` line** — line 3 was `Round:`. The stop block's template text "see below for what each mode defers to" was copied literally. $0.44 | ✗ on two counts (see Verdict) |
| P2 same fixture, after the fixes | first three lines `Result:` / `Verdict:` / `Loop:`; round 2 with prior fixed continues; zero-volume drop WARNING + `— noted` | `Result: done` / `Verdict: approve with fixes` / `Loop: converging` as the first three lines; `Round: 2`, `Convergence: 0 prior unfixed, 0 new`; the zero-volume drop graded kind 3, downgraded to WARNING as outside the diff and filed `— noted 2026-09-22, see …-ingest-2.md`; docstring, `l`, missing test WARNING; malformed-row SUGGESTION; next command `/dev-team:finalize-package data`; commit `e574d81` holds only the report and `docs/followups.md`. $0.43 | ✓ |

## Verdict

Holds after two fixes, 11/11 on the re-run. The mechanical cases and the forbid probe passed
first time. P1 exposed two defects in the change itself, both fixed in `agents/reviewer.md`
before P2:

1. **The `Loop:` line was dropped for the second time** (eval O's O2 was the first). The
   return-message rule named it in prose; it is now a three-line fenced template that opens
   the return, with `Round:` explicitly placed after it. P2 emitted all three in order.
2. **The round-2 "as many new findings as before" test stopped a healthy loop.** One fixed
   finding and one fresh one is the normal second round of a section, not divergence. The
   rule is now: round 2 stops only when a prior finding is unfixed; round 3 always. Three
   rounds is the budget, two when the fix did not take. Eval O's O1 (round 2, one prior
   unfixed) still stops under the new rule.

One thing not fixed, recorded as a watch: P1 and P2 graded the same planted defect
differently — kind 1 (a contract break: the contract names the behavior) versus kind 3 (a
wrong result), and the re-review downgrade applies only to kind 3. Both readings are
defensible; the fixture is the ambiguity. The closed list held either way: nothing outside it
was graded CRITICAL in either run, and the docstring, the name and the comprehension landed
at WARNING and SUGGESTION both times.
