---
name: status
description: Print the checklist of where every package and section stands - planned, built, reviewed since its last build, open follow-ups, decision markers - derived from docs/ and the code, never from a status file. Use before /dev-team:finalize-package, before planning the next package, or whenever you have lost track of what is done.
argument-hint: "[pkg] [--gate] [--plan-gate <pkg>] [--run-gate]"
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
commit touches `docs/packages/<pkg>/`, and its verdict is `approve` or `approve with fixes`; no
open review-sourced follow-up is addressed to `<pkg>/plan`; and no `D<n>` binding the package
is `open` with no `Assumption if unanswered:`. Every package also shows a `plan:` line — the
newest plan review's date, verdict and `@<sha>`, or `unreviewed` — or, while
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
"open followups" counts unchecked `docs/followups.md` entries addressed to that section, with
review-sourced ones (CRITICAL findings) counted separately because those block finalizing.
The `intent` column runs the tester's suite, `tests/intent/<section>/`, and shows
`<pass>/<total>`, or `—` when `/dev-team:test-section` has not run; the finalize gate does not
read it — the reviewer does.
