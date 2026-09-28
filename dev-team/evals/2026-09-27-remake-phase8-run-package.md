# remake phase 8 — run-package drives the ready set from derived state

**Tested against:** uncommitted — see working-tree diff (on `b4dd3aa`; `skills/run-package/SKILL.md` rewritten, the six agents' Inputs lists in `agents/{designer,tester,implementer,reviewer,researcher,architect}.md`, `contracts.yml`) · model: `claude-opus-5-5` (the phase, 8.1, 8.3), the 8.2 headless driver sessions `claude-sonnet-5` (every agent they spawned inherits it), graders `claude-sonnet-5` · 2026-09-27
**Set:** `evals/sets/run-package.json` evals 1, 2, 3 · **Iteration:** `evals/workspace/run-package/iteration-1`, `evals/workspace/run-package/iteration-2` (after one fix), `evals/workspace/run-package/iteration-3` (after a second fix, on the user's call) · **Baseline:** `b4dd3aa` (`skills/run-package/SKILL.md` identical to the merge-base with `main`, the 0.6 driver) · **Pass rate:** iteration 1 90% (18/20) vs 55% (11/20, the eval-2 baseline contaminated); iteration 2 90% (18/20) vs 25% (5/20, clean); iteration 3 90% (18/20) vs 30% (6/20)

## What was tested

- **8.1** — the seven planned claims (the state vocabulary, one spawn-field claim per agent, the rewritten review-loop exit), and the note's plant, `Focus: correctnes`, in a scratch driver.
- **8.2** — `/dev-team:run-package data ingest` walks one section to DONE with one commit per agent run. A designer `spec-change:contract` routes to the architect at PLAN. A BLOCKED decision is asked once and recorded as `Decision:`.
- **8.3** — the driver holds no procedure and points at no skill file.

## Method

- **8.1** — `contract_sweep.py` on the working tree. Plants go into an rsync copy of the bundle in the scratchpad, one at a time:
  - (A) `Focus: correctnes` in the driver's reviewer text;
  - (B) a reviewer field renamed `**Focuss**` in the driver;
  - (C) `on \`request changes\`, spawn the implementer` appended to the driver, and a `run` variant appended to `reviewer.md`;
  - (D) `**FIX n**` renamed `**FIX**` in `status.py`'s docstring;
  - (E) the architect's `**Spec-change**` renamed in its Inputs.
- **8.2** — real headless runs, not proxy executors. In this session `dev-team:<agent>` resolves to the installed 0.6.0 plugin, so an executor subagent acting as the driver would have spawned 0.6 agents. Each configuration was run as follows:
  - **Setup.** A fresh `reset.sh` copy of `evals/fixtures/two-package/` in the scratchpad, seeded per the eval's harness. A committed `.claude/settings.json` disables the installed dev-team.
  - **The session.** `claude -p "/dev-team:run-package data ingest" --plugin-dir <P> --model sonnet --output-format stream-json --verbose --permission-mode bypassPermissions --disallowedTools AskUserQuestion --append-system-prompt <H>`, run from the copy. `<P>` is the working tree for `with_skill`. For `old_skill` it is a scratch copy of the working-tree plugin with `skills/run-package/` replaced by the snapshot's. `<H>` tells the session it is the driver and substitutes `AskUserQuestion` with an append to `outputs/interview.md`, answered from the harness's **Answers** section, which is inlined.
  - **Outputs.** `outputs/spawns.md` (main-thread Agent calls grouped by assistant message id as the batch, plus the return's first line), `status-log.txt` and `transcript.md` (the driver's own tool calls) were derived mechanically from `stream.jsonl`. `summary.md` is the final `result` text. `git-log.txt`, `git-status.txt`, `status-final.txt` and `repo/` are read-only copies. The runner is `run.sh` and `post.py`, both in the session scratchpad.
  - **Scope.** The hooks fired: the session cwd was the copy, which has `docs/architecture.md`. One run per configuration.
  - **Cost.** with_skill $4.84 + $6.03 + $5.93; old_skill $0.76 + $6.89 + $0.60, about $25 in total.
- **Graders.** One per run, `claude-sonnet-5`, using the skill-creator grader. Each was told how the transcript was derived and allowed to read `stream.jsonl`.
- **8.3** — `grep -c 'Procedure: open' skills/run-package/SKILL.md`, plus the note's **Done when** greps.

## Results

| Case | Expected | Observed | Pass |
|---|---|---|---|
| 8.1 | all PASS | 37/37: the 29 existing claims plus 8 new ones (7 planned and the value claim) | yes |
| 8.1 plant A `Focus: correctnes` | FAIL | Passed 36/36 against the 7 planned claims: a headings claim compares names, not values. With the added `forbid` value claim it fails at `skills/run-package/SKILL.md:153` | yes, after one fix (Deviation) |
| 8.1 plant B `**Focuss**` | FAIL | reviewer field claim: `names 'Focuss'` | yes |
| 8.1 plant C, both files | FAIL | exit claim at `SKILL.md:292` and at `reviewer.md:367` | yes |
| 8.1 plant D | FAIL | vocabulary claim: `names 'FIX n'` | yes |
| 8.1 plant E | FAIL | architect field claim: `names 'Spec-change'` | yes |
| 8.2 eval 1, with_skill | 7/7 | 7/7 | yes |
| 8.2 eval 1, old_skill | — | 2/7: spawned a tester first with `Procedure: open`, and the tester returned `Result: blocker` (no design) | — |
| 8.2 eval 2, with_skill | 7/7 | 6/7. The tester's commit `3c45a63` has no `Dev-Team-Run:` trailer, though its block carried `Run: run-package data` | no |
| 8.2 eval 2, old_skill | — | 5/7. Contaminated: its plugin copy held `evals/sets/`, and the session read `harness-2-spec-change-contract.md`, then built spawn blocks from the working-tree agents' Inputs. It made two tester commits and wrote no `agent runs:` line | — |
| 8.2 eval 3, with_skill | 6/6 | 5/6: the two round-1 reviewers were spawned in two messages (batches 17 and 18), not one | no |
| 8.2 eval 3, old_skill | — | 4/6: asked D1 once and recorded it, then stopped at `integration.md` with no spawn | — |
| 8.3 | 0 | `Procedure: open` 0. `subagent_type: "dev-team:` lines 7 (≥ 6). `integration.md\|Spine\|Dependency order` 0 | yes |

The 8.2 with_skill walks:

- **Eval 1** — designer, tester, implementer, then both reviewers in batch 11: DONE, 5 commits, 961 s.
- **Eval 2** — designer `spec-change`; architect with `Package: data`, `Run: run-package data` and `Spec-change: data/ingest — 2026-09-27 — spec-change:contract`; history copy; entry `resolved`; a second designer, then on to DONE. 7 commits, 1148 s.
- **Eval 3** — asked once and recorded `Decision:` and `Status: decided` on D1; BLOCKED, then DESIGN; walked to DONE through a FIX 1 round (implementer, then a `full` reviewer with `Diff: 44658bf..HEAD`). 7 commits, 1251 s.

Also observed, not graded:

- In eval 2 as well, the round-1 reviewers went out in two messages (batches 15 and 16). So 1 of 3 runs batched them as specified.
- Eval 2's architect return began `Committed. Summary:`, with `**Result: done**` on line 3. The driver read on and continued, rather than treating the return as a block as the skill says.
- Eval 2's summary heading was `run-package data ingest: done`, and it had an `uncommitted: none` line. Eval 3's summary said `uncommitted: docs/decisions.md` although the implementer's commit had already carried the edit.

## Verdict

- **8.1 and 8.3 hold.** 8.1 needed one fix: the note's plant is a bad value, and the planned claims check names, so an eighth claim was added.
- **8.2 misses its bar** (every expectation passes for `with_skill`) on two expectations:
  1. **Round-1 reviewers not batched** (eval 3, and also seen in eval 2). This is the driver's defect, within this phase's Files. The loop's step 4 says "all of one kind in one message", but the parallel pair sits inside the REVIEW kind and is easy to serialize.
  2. **Tester commit without its trailer** (eval 2). This is `agents/tester.md`, outside this phase's Files. It is not the driver's defect: the block carried `Run:`.
- **Expectation corrected**, per the eval-1 grader's critique: "none has a **Deferred** heading" can never pass, since the reviewer writes every heading and fills an empty one with `- none`. It now reads "each one's **Deferred** heading is absent or reads `- none`", in eval 1 and in eval 4, which had the same wording. No verdict changed, so there was no rerun.
- **Baseline caveat.** The eval-2 baseline's contamination inflates it, which makes the comparison conservative. Later `old_skill` plugin copies must exclude `evals/`.

## Iteration 2 — after one fix

**The fix.** Iteration 1's miss was the driver's round-1 reviewers going out in two messages. The fix is inside the note's Files (`skills/run-package/SKILL.md`):
- The reviewer block now says the round-1 pair is "two Agent calls in the same assistant message: never one, then its return, then the other".
- Loop step 4.6 says every reviewer of the batch, both of a round-1 pair included, is an Agent call in that one message.

`check-contracts` 37/37 and `build-site` ran again after the edit.

**What changed in the method.** Both configurations now load a scratch copy of the plugin with `evals/` removed: `plugin-new-2` for with_skill, and `plugin-old-2` with the snapshot's `skills/run-package/` for old_skill. Iteration 1's eval-2 baseline had read its own harness file. The rest of the method is unchanged: fresh fixture copies, the same harness prompt and runner, `claude-sonnet-5` headless, graders `claude-sonnet-5`. Cost: with_skill $7.61 + $9.05 + $4.65; old_skill $0.64 + $1.01 + $0.59; about $24.

| Case | Expected | Observed | Pass |
|---|---|---|---|
| eval 1, with_skill | 7/7 | 6/7. Designer, tester, implementer, then the r1 pair in **one** batch (13); FIX 1; a `full` r2 reviewer; DONE, 7 commits, all trailered. Miss: the summary's first line is `run-package data ingest: done`, not `run-package data:` (the template is `run-package <pkg>:`) | no |
| eval 1, old_skill | — | 1/7: tester first with `Procedure: open`, `Result: blocker` | — |
| eval 2, with_skill | 7/7 | 7/7. Designer `spec-change`, then the architect with the `Spec-change:` line, a second designer, tester, implementer, the r1 pair in **one** batch (15); r1-b `request changes` (1 CRITICAL: an uncaught `IndexError` on short rows); FIX 1, a `full` r2 reviewer, DONE. 9 commits, all trailered | yes |
| eval 2, old_skill | — | 0/7: clean this time. No design step, the tester returned `design-gap`, stop | — |
| eval 3, with_skill | 6/6 | 5/6. It asked once, recorded D1 and walked to DONE (5 commits, all trailered). Miss: the r1 pair again went out in two messages (18, then 19). The driver wrote "spawning both reviewers … in parallel", emitted one call, and then wrote: "I should have sent both round-1 reviewers in the same message; only the conformance one went out" | no |
| eval 3, old_skill | — | 4/6: asked and recorded D1, then stopped at `integration.md` | — |

**Expectation corrected.** Eval 1 expectation 4 said "each with `Verdict:` on its second line". That confuses the reviewer's return (line 2 `Verdict:`) with its report file, whose header per `review-report.md` is title, `Scope:`, `Commit:`, `Verdict:`. It now reads "a `Verdict:` header line after `Scope:` and `Commit:`, as the review-report template orders them". The rewrite changes one verdict: iteration 2's eval 1 with_skill, from 5/7 to 6/7, regraded by hand (the evidence is in its `grading.json`). The iteration-1 grader had already read the clause that way.

**Verdict after the fix.** The bar (every with_skill expectation) is still missed.
- Reviewer batching: 2 of 3 runs batched the pair, against 1 of 3 before. Eval 3 missed it with the instruction understood and acknowledged. This is a limit of how the driver emits tool calls, not a gap in the prompt's wording.
- New miss: the summary's first line carries the section on a section walk. Iteration 1's eval 2 did the same, but no expectation there checks it.

The tester's missing trailer (iteration 1, eval 2) did not recur: every commit in all three with_skill runs carries `Dev-Team-Run: run-package data`.

Both remaining misses are recorded in the note's Deviations, and the phase is committed only on the user's yes.

## Iteration 3 — after a second fix, on the user's call

**The fix** (`skills/run-package/SKILL.md`, the user's pick from three options):
- **Summary heading.** Its first line is now `run-package <arguments as typed>:`, with examples, so a section walk reads `run-package data ingest: done`.
- **Reviewer pair.** The block keeps "two Agent calls in the same assistant message". It adds what must hold when only one went out: spawn the other next, before any other spawn or `status.py` run, with the same round and `Diff:`, and hand neither the other's report. Parallelism is speed; the independence of the two reviews is what matters for correctness.

**Expectations changed with it** (in `evals/sets/run-package.json`):
- Eval 1 expectation 2 and eval 3 expectation 4 accept the pair "in one message batch, or in consecutive batches with no other spawn and no `status.py` run between them … both with `Round: 1`, and neither prompt naming the other's report".
- Eval 1 expectation 7 wants the first line `run-package data ingest:`.
- Eval 4's `run-package <pkg>: done` still holds, since it runs with no section.

`check-contracts` 37/37 and `build-site` ran again.

**Method.** with_skill only, the same runner, a fresh `plugin-new-3` copy without `evals/`, `claude-sonnet-5`. The baseline file is unchanged, so iteration 2's old_skill outputs were copied into iteration 3 and regraded under the changed expectations. One of those regrades was completed by hand: the eval-1 grader returned six items, and the seventh, the summary expectation, is a FAIL (no `agent runs:` line). Cost: with_skill $5.14 + $5.01 + $4.70.

| Case | Expected | Observed | Pass |
|---|---|---|---|
| eval 1, with_skill | 7/7 | 7/7. The pair in one batch (12); `run-package data ingest: done`; DONE, 5 commits, all trailered | yes |
| eval 2, with_skill | 7/7 | 6/7. Routing, PLAN, a second designer and the pair in one batch (17), DONE. Miss: the tester's commit `f02d907` (`data/ingest: 17 intent tests from design`) again has no `Dev-Team-Run:` trailer | no |
| eval 3, with_skill | 6/6 | 5/6. Asked once, D1 recorded, the pair in one batch (16), DONE. Miss: no `uncommitted: docs/decisions.md` line. The driver edited the file, and the implementer's commit `9273144` then carried it, so nothing was left uncommitted. The skill says to list it whenever the driver edited it | no |
| old_skill (reused, regraded) | — | 2/7, 0/7, 4/6 | — |

**Verdict.** Both targeted misses are gone: the pair was batched in 3/3 runs and the heading echoed in 3/3. The bar is still missed on two expectations:
- **The tester's trailer.** This is now 2 of 6 tester runs across the iterations. It belongs to `agents/tester.md`, outside the phase, and is logged in the ledger.
- **The summary's `uncommitted:` line.** Present in 2 of 3 eval-3 runs across the iterations, and omitted here once the file had been committed by an agent.

The grader argued the `uncommitted:` expectation should allow for that case. It was not changed: the note's **Decisions** list the file whenever the driver edited it, and a change would be to the design, which is the user's call.

