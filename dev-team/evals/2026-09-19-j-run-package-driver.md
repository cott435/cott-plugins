# J — `run-package`: the driver runs the loop, stops on the right gates, duplicates no skill text

**Tested against:** uncommitted — see working-tree diff (phase 8 of the 0.5 overhaul, on top of
`7b3ae38`): `skills/run-package/SKILL.md` (new), `skills/status/scripts/status.py`,
`skills/status/SKILL.md`, the `Result:` sentinel in `agents/architect.md`, `implementer.md`,
`tester.md` and `reviewer.md`, the **Invoked by run-package** paragraph in eight forked skills,
`agents/tester.md`'s lint rule, `pyproject-lint-config.toml`, `contracts.yml` · model:
`claude-sonnet-5` (the CLI default in the headless runs; every agent on `inherit`; each run's
`modelUsage` shows only `claude-sonnet-5`, except run 5, whose stub agents were pinned to
`claude-haiku-4-5-20251001`); `claude-opus-5` ran the checks · Claude Code `2.1.270` · 2026-09-19

## What was tested

Note 09 eval J, the three runs in note 08 §Steps 6 plus its Done-when grep. (i) In full mode on
a reviewed plan, the driver runs tester → implementer → tester → reviewer per section, in
dependency order, then finalize → review-package → sync-design, and ends `done` with a
sync-design commit at HEAD. (ii) In spine mode it builds the spine, completes and reviews the
plan, and stops with the decisions message. (iii) A CRITICAL the implementer cannot fix stops
the run at implementer run 3 with the right `next`. Also covered: `status.py --run-gate`
mechanically, and the `contracts.yml` claim this phase added.

## Method

**Behavioral**: real headless runs, `claude -p "<command>" --plugin-dir <abs>/dev-team
--output-format stream-json --verbose --permission-mode bypassPermissions`, on a `reset.sh`
copy of the fixture (with `docs/constraints.md`) on branch `build`. Spawns and their prompts
come from the driver's own `Agent` tool calls in the stream; commits come from git.

| Run | Command | Repo | Cost | Result |
|---|---|---|---|---|
| 0 | `/dev-team:plan-repo` | fresh fixture | $0.87 | `e3145a3` |
| 1 | `/dev-team:plan-package data` | same | $0.67 | spine run, `10c2efd`, run gate `PASS (mode: spine)` |
| 2 | `/dev-team:run-package data` — **(ii)** | same | $10.43 | 7 section spawns, then the architect and `review-plan`; 8 commits; stop message |
| — | manual intervention | same | — | `0993392`: root `pyproject.toml` `extend-exclude = ["docs"]`, and the 3 `data/ingest` follow-ups that `ba4bf31` had already fixed ticked (see Results) |
| 3 | `/dev-team:run-package data` — **(i)** | same | $12.15 | 11 spawns, 9 commits; stopped at `sync-design` (see Results) |
| 4 | `/dev-team:run-package data` — **(iii)**, real seed | copy of the post-intervention repo, with an uncommitted Enforced row requiring `clean_v2` in `contract.md` | $1.41 | implementer `blocked` at run 1 |
| 5 | `/dev-team:run-package data` — **(iii)**, stub agents | clone at `0993392`; plugin copy with `haiku` stub tester, implementer and reviewer (the reviewer always returns `request changes`) | $0.52 | stopped at implementer run 3 |
| 6 | `/dev-team:run-package data` — resume of (i) | run 3's repo | $0.58 | 1 spawn (`sync-design`), `done`, `6ced9f8` |
| 7 | `/dev-team:run-package data` — no-op | same | $0.31 | 1 spawn, 0 commits, `done` |

Total $26.94. Runs 3 and 4 ran in parallel on separate repos. Runs 2–4 used the spawn block's
first wording ("as if you had been invoked as"), and runs 5–7 the fixed one. The copies needed
`uv sync --all-packages`: a copied `.venv` points its editable install at the original repo
(0 % coverage).

**Mechanical**: `status.py data --run-gate` on a copy of the run-1 repo — the baseline, the
three exempt files edited, a stray file plus a staged rename, a modified tracked file, `main`,
a missing `integration.md`, and a spine plan edited to `complete` with and without
`surface.md` — plus `--run-gate` with no package and outside a repository.
`contract_sweep.py` on the real files, and with a planted `subagent_type: "tester"` in the
driver. The Done-when grep splits the driver body into sentences and looks each one up in
`implement-section/SKILL.md`.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| (ii) spine: order of spawns | tester, implementer, tester, reviewer on `ingest` | exactly that; the review requested changes (4 CRITICAL), so implementer run 2, tester, reviewer, then `approve` | ✅ |
| (ii) spine: completion and plan review | architect `plan-package` (completion run), reviewer `review-plan` | both; `1f829f4` with 2 designs + `surface.md`, `4ac5aff` plan `approve` | ✅ |
| (ii) spine: stops for decisions | the step-4 message; no build of `clean` | message printed, nothing further spawned | ✅ |
| (ii) summary | six-line block with `next` | first line `done`, no `next:` line, message printed after the block | ❌ → fixed, not re-run |
| every spawn | `dev-team:<agent>`, foreground, the verbatim block | all 33 across runs 2–7; `run_in_background: false` on each | ✅ |
| trailers | one commit per agent run, each with `Dev-Team-Run:` | yes, including the implementer's second run | ✅ |
| (i) full: skip | `ingest` skipped (reviewed `approve`, `(0 review)`, `19/19`) | skipped | ✅ |
| (i) full: per-section order | `clean` then `storage`, each tester → implementer → tester → reviewer | exactly that; both `approve` first time | ✅ |
| (i) full: close-out | finalize → review-package → sync-design | finalize `54c1ab4`, package review `approve` `b01508c`; the **sync-design architect called the Skill tool** on `dev-team:sync-design`, was refused (`disable-model-invocation`: "do not replicate this skill's workflow"), and returned `blocked` | ❌ → fixed |
| (i) stop on `blocked` | stop, `next: /dev-team:sync-design data` | exactly that | ✅ |
| resume gate | run gate passes after finalize | **FAIL: plan not reviewed since last change** (`interface.md` sits under `docs/packages/data/`) | ❌ → fixed |
| resume skip | approved `storage` skipped | intent column `18/19`: the 1 is an `xfail` for open D2, which the rule counted as a failure, so `storage` would have been rebuilt | ❌ → fixed |
| (i) resume after the fixes (run 6) | skip everything, run sync-design, `done`, sync-design at HEAD | 1 spawn; the architect read the file, didn't call the Skill tool, folded 2 deviations; `6ced9f8` at HEAD with trailer `sync-design data`; `done` | ✅ |
| run 6 `next` | `/dev-team:plan-package analysis` | the architect's placeholder copied: `plan-package <next package in …>` | ❌ → fixed |
| run 7 `next` | `/dev-team:plan-package analysis`, 0 commits | exactly that | ✅ |
| (iii) real seed | a CRITICAL the implementer can't fix | the implementer returned `blocked` at run 1 (it cannot pass the Enforced row); the driver stopped with `next: /dev-team:implement-section data/clean` | ✅ for the blocked path; the cap was not reached |
| (iii) real seed: step 3.1 | tester intent first | **the driver went straight to the implementer** | ❌ → fixed |
| (iii) stub cap (run 5) | T, I, T, R, I, T, R, I, T, R, stop at implementer run 3 | exactly that sequence; `stopped at data/clean review-section (implementer run 3)`; `next: /dev-team:implement-section data/clean`; all six summary lines | ✅ |
| run gate, 9 mechanical cases | PASS spine / PASS with exempt edits / FAIL ×6 / usage error | all as expected after one fix: the first version printed `ocs/decisions.md` (the `git()` helper strips output, eating the first porcelain line's leading space), and so failed the exempt case | ✅ after fix |
| contracts, real files | 22/22 | 22/22 | ✅ |
| contracts, planted bare spawn | the new claim fails | `FAIL … skills/run-package/SKILL.md:146` | ✅ |
| Done-when grep | 0 shared sentences | 0 of 61 | ✅ |

What the manual intervention was for: after run 2, `status.py` read `ingest` as `3 (0 review)`
follow-ups. Two were really review-sourced, but `review` sat on a wrapped continuation line. And
the repo's `ruff format` Floor row failed on Python blocks inside `design/*.md`, which no run
may edit. Both are fixed in the plugin (`open_followups` reads whole entries;
`pyproject-lint-config.toml` excludes `docs`). The tester now formats and lints its own tree,
because nobody else may. The intervention did in the fixture what a user would have done.

## Verdict

Holds after six fixes, five of them re-run. (i) passes as two invocations: run 3 did every
section and the finalize/review close-out, then stopped correctly on the `sync-design`
architect's `blocked`. Run 6, with the fixed spawn block, did `sync-design` and ended `done`
with its commit at HEAD. (ii) passes on behavior. Its summary-format fix (always `next:`, a
spine run is a stop, nothing after the block) was not re-run in spine mode. Runs 5–7 show the
same rules holding in full mode. (iii) passes on stub agents; the real seed is logged as a pass
for the blocked-stop path. The skip rule, the step-3.1 intent check and the summary block were
all exercised in run 5.

The platform refusal in run 3 matters beyond this driver. Workflow skills are
`disable-model-invocation`, and the Skill tool says not to replicate them "by other means".
The driver does exactly that on purpose, from a command the user typed. It works because the
spawn prompt names the file to Read and says the user's `/dev-team:run-package` authorizes the
step. If the platform ever enforces that sentence rather than stating it, the driver's design
(note 08 §Reusing the skills) has to change.

Watch in phase 9: the implementer blocks rather than loops on a CRITICAL it can't fix, so the
cap mostly guards reviewer/implementer disagreement. Nothing ticks a follow-up about the
tester's tree once the tester's fix lands. `.claude/agent-memory/` stays untracked, and the run
gate now exempts it. The spine build cost $10.43 with one review round-trip.
