# I — spine-first package planning: spine selection, too-early return, completion run with `Sibling shipped:`, `--all`

**Tested against:** uncommitted — see working-tree diff (phase 7 of the 0.5 overhaul, on top of
`c08120e`): `agents/architect.md`, `agents/designer.md`, `skills/plan-package/SKILL.md`,
`skills/planning-templates/references/integration.md`, `skills/review-plan/SKILL.md`,
`skills/status/SKILL.md`, `skills/status/scripts/status.py`, `contracts.yml` · model:
`claude-sonnet-5` (CLI default in the headless runs; every agent on `inherit`, and every run's
`modelUsage` shows only `claude-sonnet-5`); `claude-opus-5` ran the checks · Claude Code
`2.1.270` · 2026-09-19

## What was tested

Note 09 eval I, the four checks in note 07 §Steps 5, on the fixture's `data` package
(`ingest`; `clean` depends on `ingest`; `storage` depends on `clean`): (i) the first
`plan-package data` designs exactly `ingest` and writes no `surface.md`; (ii) a second run
before the spine is built returns the *too early* message and writes nothing; (iii) after the
spine ships, the completion run spawns exactly two designers, both with `Sibling shipped:`
naming the `ingest` README, and writes `surface.md`; (iv) `--all` on a fresh copy designs all
three in one run. Also note 07 §Done when: `review-plan` on a spine-only plan returns the
blocker, and `status.py` prints the spine line.

## Method

**Behavioral**: real headless runs, `claude -p "<command>" --plugin-dir <abs>/dev-team
--output-format stream-json --verbose --permission-mode bypassPermissions`, on a `reset.sh`
copy of the fixture (with `docs/constraints.md`) on branch `build`. Designer counts come from
each run's `subagent_stats.by_type`; the designer prompts from its `task_started` events; the
rest from git and the files.

| Run | Command | Cost | Result |
|---|---|---|---|
| 0 | `/dev-team:plan-repo` | $0.77 | `6d3279d`; the repo was copied here for run 4 |
| 1 | `/dev-team:plan-package data` | $0.75 | `e22edd5`, 1 designer |
| 1b | `/dev-team:review-plan data` | $0.16 | blocker, nothing written |
| 2 | `/dev-team:plan-package data` | $0.15 | too early, nothing written |
| 3a–d | `test-section`, `implement-section`, `test-section`, `review-section data/ingest` | $0.65 + $4.21 + $0.31 + $1.07 | `8bc8fc8` 28 intent tests, `e595fa4` build, `66fc5b0` reconcile (0 changed), `1a1c211` approve with fixes |
| 4 | `/dev-team:plan-package data --all` on the run-0 copy | $0.84 | **spine run**: 1 designer, no `surface.md` (`3c511b3`) |
| 4b | same, after the flag fix, from `6d3279d` with `.claude/` removed | $1.36 | `ba51451`, 3 designers |
| 5 | `/dev-team:plan-package data` (completion) | $0.91 | `5008d58`, 2 designers |

Total $11.18, most of it the spine build (3a–d), which the check needs but does not test.
Runs 1, 1b and 2 used the first version of the flag paragraph in `plan-package`; runs 4b and 5
used the fixed one. The fix touched only that paragraph and step 4c's first sentence.

**Mechanical**: `status.py data` and `status.py --plan-gate data` after run 1. `contract_sweep.py`
on the real files, and with the integration claim's owner span moved back to
`1. **Contract deviations**` (the planted defect: **Spine** not in the template).

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| (i) spine run designs exactly `ingest` | 1 designer, `design/ingest.md` only | `{'dev-team:designer': 1}`; `design/` holds `ingest.md` | ✅ |
| (i) no `surface.md` | absent | absent; commit = contract, `design/ingest.md`, `integration.md` | ✅ |
| (i) **Spine** heading | `spine only`, `ingest`, 2 of 2, pending `clean, storage` | exactly that | ✅ |
| (i) **Dependency order** lists all three | ingest, clean, storage | yes | ✅ |
| (i) return | four spine commands, then `plan-package data` | yes, in that order | ✅ |
| `status.py` spine line | `plan: spine only (ingest) — …` | `plan: spine only (ingest) — build it, then re-run plan-package` | ✅ |
| `--plan-gate` on spine-only | FAIL, spine-only reason | FAIL, one reason: `plan is spine-only (ingest)` | ✅ |
| `review-plan` on spine-only | note 05's blocker, nothing written | the blocker verbatim; it said the check ran before the `surface.md` check; tree unchanged | ✅ |
| (ii) too early | message, no write, no commit | message returned, HEAD unchanged, tree clean except `.claude/` agent memory | ✅ (see wording) |
| (ii) message wording | spine named | `Spine <ingest> is designed…`: brackets left in | ⚠ → fixed |
| (iii) completion: 2 designers | `clean`, `storage` | `{'dev-team:designer': 2}`, `data/clean` and `data/storage` | ✅ |
| (iii) both prompts carry `Sibling shipped:` | the ingest README | both `Sibling shipped: packages/data/src/data/ingest/README.md`; `clean.md` cites that README by path | ✅ |
| (iii) `surface.md` and **Spine** | exists; `complete`, `Section: ingest` kept | both | ✅ |
| (iii) return | next `/dev-team:review-plan data` | yes | ✅ |
| (iv) `--all`, first version | 3 designers | **1: a spine run**. The substituted skill read *"Read the flags from `data --all` itself, not from `--all`"* | ❌ → fixed |
| (iv) `--all`, after the fix | 3 designers, `surface.md`, `Status: complete`, `Section: —` | `{'dev-team:designer': 3}`, all four, trailer `plan-package data --all` | ✅ |
| contracts, real files | 21/21 | 21/21 | ✅ |
| contracts, planted defect | integration claim fails on `Spine` | FAIL: `review-plan/SKILL.md names 'Spine'; architect.md names 'Spine'` | ✅ |

## Verdict

Holds, 4/4, after one fix. `--all` failed first because the flag paragraph named `$ARGUMENTS`
and `$flags`, which substitution turned into a sentence that contradicted itself. The skill now
opens with the substituted arguments on their own line and one bullet per flag, and step 4c
checks `--all` before anything else. A re-run from the same post-`plan-repo` commit, with the
first run's agent memory removed, designed all three sections. The too-early message's leftover
angle brackets were fixed in the architect's prompt and not re-run, since the wording is
cosmetic.

Watch in phase 9: the architect's project memory (`.claude/agent-memory/`) stays untracked in
the eval repo after every run, and no baseline check tripped on it. The run-1 architect
resolved all three designer OQs in `integration.md` and wrote no `decisions.md`, which the
note 05 rule allows. `implement-section` on the spine cost $4.21, the largest single run so far.
