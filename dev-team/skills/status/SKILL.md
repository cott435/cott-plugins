---
name: status
description: Print the checklist of where every package and section stands - planned, built, reviewed since its last build, open follow-ups, decision markers - derived from docs/ and the code, never from a status file. Use before /dev-team:finalize-package, before planning the next package, or whenever you have lost track of what is done.
argument-hint: "[pkg] [--gate] [--plan-gate <pkg>] [--run-gate] [--rounds <target>]"
disable-model-invocation: true
---

Run the status script from the repo root and show its output verbatim:

```
python3 ${CLAUDE_SKILL_DIR}/scripts/status.py $ARGUMENTS
```

Then, in two or three lines, say what the table means for the next command: which section is
next in order, which sections still need a review before `/dev-team:finalize-package`, which package
is ready to plan against. Do nothing else — no edits, no fixes.

With a package name, only that package is shown. With `--gate`, the script also prints the
`/dev-team:finalize-package` preconditions as PASS or FAIL with reasons — the same check that skill
runs before building the surface. When `docs/constraints.md` exists, the gate also runs its
**Floor** and **Enforced** rows for the package — `repo` rows once, `package` rows with `<pkg>`
substituted, no shell, from the root, ten minutes each — and prints one line per failing row,
`<pkg>: constraint <dimension> FAIL (<command>)`. Every package with code shows a
`constraints:` line — `<n> enforced, <k> failing`, or `no docs/constraints.md`. With `--plan-gate <pkg>`, it prints `plan gate: PASS|FAIL`
with reasons: the contract, `integration.md` and `surface.md` exist and the plan is not
spine-only; the newest `docs/reviews/<date>-<pkg>-plan.md` has a `Commit:` after which no
commit touches the documents that review covers — the contract, `design/`, `integration.md`
and `surface.md`, counting neither `interface.md` nor a `sync-design` commit — and its
verdict is `approve` or `approve with fixes`; no
open review-sourced follow-up is addressed to `<pkg>/plan`; and no `D<n>` binding the package
is `open` with no `Assumption if unanswered:`. It ends with `plan rounds since last approve:
<n>` — consecutive `request changes` plan reviews since the last approving one, the count
`/dev-team:review-plan` numbers its rounds from and stops the plan-and-review loop on; a
`request changes` gate line carries the round, and `not converging` from round 3. With
`--rounds <pkg>`, `--rounds <pkg>/<section>` or `--rounds <pkg>/surface`, only that scope's
`rounds since last approve: <n>` line is printed — no package report, so no test or
constraint command runs; every reviewer run asks it first, and `/dev-team:run-package` reads
it in place of a counter of its own. A section row's reviewed column and the `surface:` line
carry ` r<n>` while their count is non-zero. Every package also shows a `plan:` line — the
newest plan review's date, verdict and `@<sha>`, or `unreviewed`, with the round count
appended while it is non-zero — or, while
`integration.md`'s **Spine** heading reads `spine only`, `plan: spine only (<section>) — build it,
then re-run plan-package`. With `<pkg> --run-gate`, it prints `run gate: PASS (mode: spine|full)` or
`FAIL` with reasons — the check `/dev-team:run-package` starts with: a git repository on a branch
other than `main`/`master`; `git status --porcelain` empty but for the files
`git-workflow-and-versioning` §Project convention exempts under **Baseline**; `contract.md` and
`integration.md` present; then `mode: spine` when the **Spine** heading reads `spine only`, else
every `--plan-gate` condition, and `mode: full`.

Everything printed is derived: a package is *planned* when `contract.md` exists, *built* when
every section has a README, *shipped* when `interface.md` exists; a section is *reviewed* when
the newest `docs/reviews/<date>-<pkg>-<section>.md` has a `Commit:` line and no commit after
that sha touches the section's source, `tests/unit/<section>/` or `tests/intent/<section>/`
(the column shows the review's date, verdict and `@<sha>`; a review with no `Commit:` line is
stale, and a section with changes git does not hold shows `uncommitted` and fails the gate);
"open followups" counts unchecked `docs/followups.md` entries addressed to that section and to
`<pkg>/<section>/intent`, as `<n> (<r> review, <i> intent)`: review-sourced ones (CRITICAL
findings) and ones in the tester's tree are counted separately because each blocks finalizing
and each has a different owner — the implementer clears a review finding, the tester an
`/intent` one.
The `intent` column runs the tester's suite, `tests/intent/<section>/`, and shows
`<pass>/<total>`, or `—` when `/dev-team:test-section` has not run; the finalize gate does not
read it — the reviewer does.
