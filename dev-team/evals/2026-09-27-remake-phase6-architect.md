# remake phase 6 — architect, plan-repo, plan-package, sync-plan

**Tested against:** uncommitted — see working-tree diff (on `48a1da6`; `agents/architect.md`, `skills/plan-repo/SKILL.md`, `skills/plan-package/SKILL.md`, `skills/sync-plan/SKILL.md`, `skills/planning-templates/`, `contracts.yml`) · model: `claude-opus-5-5` (mechanical rows, the phase), executors, graders and blind comparators `claude-sonnet-5`, the 6.3 nested `claude -p` sessions `claude-sonnet-5` · 2026-09-27
**Set:** `evals/sets/architect.json` evals 1, 2, 3 · **Iteration:** `evals/workspace/architect/iteration-1`, `evals/workspace/architect/iteration-2` · **Baseline:** `af08482` (merge-base with `main`, the 0.6 architect) · **Pass rate:** iteration 1 100% vs 100%; iteration 2 100% vs 63% · **Blind:** new preferred 2/3 (iteration 1; not run in iteration 2, the rates 37 points apart)

## What was tested

- **6.1** — the contract sweep passes with the integration, surface and `As shipped` claims deleted, the change-file claim added, the deviations-entry claim gaining the architect, and the spawn claim re-pointed; a planted bare spawn fails it.
- **6.2** — the rewritten architect WRITEs a package contract ending in the `surface` row with no designer (eval 1), classifies a two-item change as CHANGE (a change file) and EDIT+STALE with an archive copy (eval 2), and closes a package by syncing only what verifies against the code (eval 3). Bar: every expectation passes for `with_skill`; `old_skill` fails the `surface` row, the CHANGE outcome and the `synced` status.
- **6.3** — `/dev-team:sync-plan data`, typed, loads and runs in a `state-cases` `shipped` build: `Result: done` and a commit with `Dev-Team-Run: sync-plan data`.

## Method

- **6.1** `contract_sweep.py` on the working tree. Plant, in a scratch copy of the plugin: `Spawn one designer per section …` under **Probing**, and `Spawn one architect per package …` at the end of `architect.md`; then the designer line rewritten prefixed (`` `dev-team:designer` per section ``).
- **6.2** `run-evals`, one run per configuration, proxy executors (a general-purpose subagent given the agent file). `old_skill` read the 0.6 `architect.md` from the baseline snapshot, and every plugin skill it read from a full `git archive af08482` extract (`iteration-1/baseline-plugin/`), so it saw its own templates (`integration.md`, `contract-delta.md`, no `change.md`). Graders on skill-creator's `grader.md`; blind comparison run automatically (pass rates equal).
- **6.3** `build.py shipped` twice into the scratchpad, each with a committed `.claude/settings.json` disabling the installed dev-team; then `claude --plugin-dir ./dev-team --model sonnet -p "/dev-team:sync-plan data"`. Build 1 is `shipped` as written (nothing to sync). Build 2 adds one committed `approved` deviation for `data/clean` whose `Did:` (`dedupe(path)`, no sorting) is the fixture's code, so the close has something to apply and commit.

## Results

| Row | Case | Expected | Observed | Pass |
|---|---|---|---|---|
| 6.1 | sweep | all PASS | 29/29 | yes |
| 6.1 | plant: bare `designer per section`, bare `architect per package` | spawn claim FAILs | FAIL at `architect.md:333`, `:464` | yes |
| 6.1 | plant: `` `dev-team:designer` per section `` | FAILs (the architect never spawns designers) | FAIL at `:333` | yes |
| 6.2 | eval 1 WRITE, surface row | with 8/8; old fails the surface row | with 8/8; **old 8/8** | with yes; baseline half no |
| 6.2 | eval 2 CHANGE + EDIT+STALE | with 7/7; old fails CHANGE | with 7/7; **old 7/7** | with yes; baseline half no |
| 6.2 | eval 3 sync close | with 9/9; old fails `synced` | with 9/9; **old 9/9** | with yes; baseline half no |
| 6.3 | `shipped` (nothing to sync) | `Result: done` and a commit | `Result: done`, `Commit: none (nothing written)` | done yes; commit n/a (Deviation) |
| 6.3 | `shipped` + one verifiable approved deviation | `Result: done` and a commit with the trailer | `Result: done`; commit `f785fed plan data: sync approved deviation into contract`, `Dev-Team-Run: sync-plan data`; contract archived to `docs/history/2026-09-27-data-contract.md`; entry `Status: synced`, `Resolved by: e2600f7`; clean tree | yes |

Blind comparison (`benchmark.md`): eval 1 old preferred (7.0 / 9.7 — the working tree stubbed D1–D3 where the harness settled them, D3 contradicting its own contract, and left the harness's `interview.md`); evals 2 and 3 new preferred (9.7 / 8.3 each — a change file closer to `change.md`; old tagged a synced citation `approved`). Eval 3's comparator also credited the working tree's commit body, which §Project convention does not allow — that reason is backwards.

Tokens: with 109k ± 1k, old 121k ± 5k per run; time 224 s vs 238 s.

## Verdict

6.1 holds. 6.3 holds on build 2; on build 1 the commit half of the bar cannot hold, since a run that writes nothing commits nothing (§Project convention rule 4), and the note is amended in its Deviations.

6.2: the working tree passes every expectation, but **the baseline half of the bar is missed**: the 0.6 architect also passes 24/24. The cause is the set, not the agent: each prompt quotes the new skill's task word for word (the `surface` row, the four outcomes, the verify-then-sync close), and a proxy executor follows the prompt whatever its agent file says. The set cannot tell the two architects apart. The blind comparison, the only signal that separates them, prefers the working tree 2/3.

**Iteration 2 (the fix, on the user's call).** The set's prompts were rewritten: each names the
forking skill and has the executor read that skill's `SKILL.md` from its configuration's own
plugin copy (the working tree, or the `af08482` extract), so the baseline gets the 0.6
`plan-package` and `sync-plan`. Same executors, graders and models; one run per configuration.

| Eval | with_skill | old_skill | What the baseline did |
|---|---|---|---|
| 1 WRITE | 8/8 | 6/8 | no `surface` row (the 0.6 architect: "never a row in a Sections table"); classified a spine run and wrote out a `dev-team:designer` spawn |
| 2 CHANGE + EDIT+STALE | 7/7 | 1/7 | filed the alias item as `docs/plans/side-aliases/` (assessment + contract-delta), no archive copy, edited the `storage` row and Package conventions too, no `CHANGE`/`EDIT+STALE` rows |
| 3 sync close | 9/9 | 9/9 | the 0.6 `sync-plan` reads `docs/plans/<slug>/`; there is none, so the executor reinterpreted the task from the fixture's ledger and change file and produced the same close |

The bar's baseline half now holds for the `surface` row (eval 1) and the CHANGE outcome (eval 2).
It still misses for the `synced` status (eval 3): a capable executor handed a 0.6 skill that
cannot apply rebuilds the new behavior from the fixture, and nothing in the expectations
distinguishes a close derived from `sync-plan` from one improvised around it. The working tree
passes every expectation in both iterations.

Also observed, not graded: eval 3's working tree wrote `Resolved by: run-package data (sync-plan), 2026-09-27`, not the sha of the approving review's `Commit:` the agent specifies (both configurations did). 6.3's run wrote a prose commit body, and its next command was `/dev-team:status`, not `/dev-team:plan-package analysis`.

Expectation corrections from the graders' critiques, no verdict changed (iteration 2: eval 2's
trailer expectation accepts the change request after `plan-package data`, as §Project convention's
"argument as typed" requires — its grader already read it as a prefix; eval 1's expectation 6
says a call written out as the one it would have made counts. That grader also called the
baseline's quote of its agent file fabricated, having checked the working-tree file; the 0.6 file
does say it, and the verdict — no `surface` row — stands). Iteration 1: eval 1's expectation 6 also requires nothing under `outputs/docs/history/` (a WRITE archives nothing); eval 2's expectation 3 drops "and its Public surface (intent) where it gives a signature" (the fixture's table carries none, so it was vacuous).
